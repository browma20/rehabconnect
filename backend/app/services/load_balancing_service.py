from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session as OrmSession
from backend.app.models.session import Session as SessionModel
from backend.app.models.therapist import Therapist
from backend.app.services.matching_service import MatchingService
from backend.app.services.conflict_detection_service import ConflictDetectionService
from backend.app.services.session_audit_service import SessionAuditService
from backend.app.services.notification_service import NotificationService


class LoadBalancingService:
    def __init__(self, db: OrmSession):
        self.db = db
        self._matching_service = MatchingService(db)
        self._conflict_service = ConflictDetectionService(db)

    def _duration_minutes(self, session: SessionModel) -> int:
        start_dt = datetime.combine(session.date, session.start_time)
        end_dt = datetime.combine(session.date, session.end_time)
        return int((end_dt - start_dt).total_seconds() / 60)

    def _build_therapist_index(self):
        therapists = self.db.query(Therapist).filter(Therapist.active == True).all()
        index = {}
        for t in therapists:
            index[t.therapist_id] = {
                "therapist_id": t.therapist_id,
                "first_name": t.first_name,
                "last_name": t.last_name,
                "discipline": t.discipline,
            }
        return index

    def _derive_load_thresholds(self, minutes_by_therapist: dict, sessions_by_therapist: dict):
        total_therapists = len(minutes_by_therapist)
        if total_therapists == 0:
            return {
                "avg_minutes": 0,
                "avg_sessions": 0,
                "overloaded_minutes_threshold": 0,
                "underloaded_minutes_threshold": 0,
            }

        avg_minutes = sum(minutes_by_therapist.values()) / total_therapists
        avg_sessions = sum(sessions_by_therapist.values()) / total_therapists

        return {
            "avg_minutes": round(avg_minutes, 2),
            "avg_sessions": round(avg_sessions, 2),
            "overloaded_minutes_threshold": round(avg_minutes * 1.2, 2),
            "underloaded_minutes_threshold": round(avg_minutes * 0.8, 2),
        }

    def _snapshot_groups(self, therapist_index: dict, minutes_by_therapist: dict, sessions_by_therapist: dict, thresholds: dict):
        overloaded = []
        underloaded = []

        overload_threshold = thresholds["overloaded_minutes_threshold"]
        underload_threshold = thresholds["underloaded_minutes_threshold"]

        for therapist_id, meta in therapist_index.items():
            entry = {
                "therapist_id": therapist_id,
                "first_name": meta["first_name"],
                "last_name": meta["last_name"],
                "discipline": meta["discipline"],
                "weekly_minutes": minutes_by_therapist.get(therapist_id, 0),
                "weekly_sessions": sessions_by_therapist.get(therapist_id, 0),
            }
            if entry["weekly_minutes"] > overload_threshold:
                overloaded.append(entry)
            elif entry["weekly_minutes"] < underload_threshold:
                underloaded.append(entry)

        overloaded.sort(key=lambda x: x["weekly_minutes"], reverse=True)
        underloaded.sort(key=lambda x: x["weekly_minutes"])
        return overloaded, underloaded

    def _ordered_candidates(self, ranked: list, underloaded_ids: set, minutes_by_therapist: dict):
        return sorted(
            ranked,
            key=lambda c: (
                0 if c["therapist_id"] in underloaded_ids else 1,
                minutes_by_therapist.get(c["therapist_id"], 0),
                -c["score"],
            ),
        )

    def balance_load(self, week_start: date, days: int = 7):
        week_end = week_start + timedelta(days=days)

        therapist_index = self._build_therapist_index()
        minutes_by_therapist = {tid: 0 for tid in therapist_index.keys()}
        sessions_by_therapist = {tid: 0 for tid in therapist_index.keys()}

        week_sessions = (
            self.db.query(SessionModel)
            .filter(
                SessionModel.date >= week_start,
                SessionModel.date < week_end,
                SessionModel.therapist_id.isnot(None),
            )
            .all()
        )

        for session in week_sessions:
            tid = session.therapist_id
            if tid not in minutes_by_therapist:
                continue
            minutes_by_therapist[tid] += self._duration_minutes(session)
            sessions_by_therapist[tid] += 1

        thresholds = self._derive_load_thresholds(minutes_by_therapist, sessions_by_therapist)
        initial_overloaded, initial_underloaded = self._snapshot_groups(
            therapist_index,
            minutes_by_therapist,
            sessions_by_therapist,
            thresholds,
        )

        actions_taken = []
        overload_threshold = thresholds["overloaded_minutes_threshold"]

        for overloaded in initial_overloaded:
            overloaded_id = overloaded["therapist_id"]

            source_sessions = (
                self.db.query(SessionModel)
                .filter(
                    SessionModel.therapist_id == overloaded_id,
                    SessionModel.date >= week_start,
                    SessionModel.date < week_end,
                )
                .order_by(SessionModel.date.asc(), SessionModel.start_time.asc())
                .all()
            )

            for session in source_sessions:
                if minutes_by_therapist.get(overloaded_id, 0) <= overload_threshold:
                    break

                match_result = self._matching_service.match_therapists_to_session(session.id)
                ranked = []
                if match_result and match_result.get("best_match"):
                    ranked.append(match_result["best_match"])
                if match_result:
                    ranked.extend(match_result.get("alternatives", []))

                ranked = [c for c in ranked if c["therapist_id"] != overloaded_id]
                if not ranked:
                    actions_taken.append({
                        "session_id": session.id,
                        "from_therapist": overloaded_id,
                        "to_therapist": None,
                        "success": False,
                        "reason": "No eligible therapists returned by matching engine",
                    })
                    continue

                _, dynamic_underloaded = self._snapshot_groups(
                    therapist_index,
                    minutes_by_therapist,
                    sessions_by_therapist,
                    thresholds,
                )
                underloaded_ids = {t["therapist_id"] for t in dynamic_underloaded}
                ranked = self._ordered_candidates(ranked, underloaded_ids, minutes_by_therapist)

                reassigned = False
                original_therapist = overloaded_id
                session_minutes = self._duration_minutes(session)

                for candidate in ranked:
                    target_id = candidate["therapist_id"]

                    session.therapist_id = target_id
                    conflict_report = self._conflict_service.detect_conflicts_for_session(session.id)

                    if conflict_report and not conflict_report["has_conflicts"]:
                        self.db.commit()
                        self.db.refresh(session)

                        minutes_by_therapist[original_therapist] -= session_minutes
                        sessions_by_therapist[original_therapist] -= 1
                        minutes_by_therapist[target_id] = minutes_by_therapist.get(target_id, 0) + session_minutes
                        sessions_by_therapist[target_id] = sessions_by_therapist.get(target_id, 0) + 1

                        # Log audit entry
                        audit_service = SessionAuditService(self.db)
                        audit_service.log_action(
                            session_id=session.id,
                            action_type="load_balanced",
                            performed_by="system:load_balancer",
                            old_values={"therapist_id": original_therapist},
                            new_values={"therapist_id": target_id},
                            notes=f"Reassigned from {original_therapist} to {target_id} for load balancing (score: {candidate['score']})",
                        )

                        # Send notifications
                        notification_service = NotificationService(self.db)
                        notification_service.notify_therapist(
                            original_therapist,
                            session.id,
                            "SESSION_REASSIGNED",
                            f"Your session for patient {session.patient_id} on {session.date.isoformat()} has been reassigned to another therapist for load balancing.",
                        )
                        notification_service.notify_therapist(
                            target_id,
                            session.id,
                            "SESSION_ASSIGNED",
                            f"You have been assigned a {session.discipline} session for patient {session.patient_id} on {session.date.isoformat()} from {session.start_time.isoformat()} to {session.end_time.isoformat()} (load balancing).",
                        )

                        actions_taken.append({
                            "session_id": session.id,
                            "from_therapist": original_therapist,
                            "to_therapist": target_id,
                            "success": True,
                            "score": candidate["score"],
                            "reason": "Reassigned successfully",
                        })
                        reassigned = True
                        break

                    session.therapist_id = original_therapist
                    self.db.expire(session)

                if not reassigned:
                    actions_taken.append({
                        "session_id": session.id,
                        "from_therapist": original_therapist,
                        "to_therapist": None,
                        "success": False,
                        "reason": "All candidates had conflicts",
                    })

        final_overloaded, final_underloaded = self._snapshot_groups(
            therapist_index,
            minutes_by_therapist,
            sessions_by_therapist,
            thresholds,
        )

        recommendations = []
        if final_overloaded:
            recommendations.append(
                "High load remains for one or more therapists; review PRN/contract coverage for this week."
            )
            recommendations.append(
                "Consider opening additional availability windows or reducing low-priority visits."
            )
        if final_underloaded:
            recommendations.append(
                "Underloaded therapists are available; prioritize them for new or open sessions."
            )
        if not recommendations:
            recommendations.append("Load appears balanced across active therapists for the selected window.")

        return {
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "days": days,
            "thresholds": thresholds,
            "overloaded_therapists": final_overloaded,
            "underloaded_therapists": final_underloaded,
            "actions_taken": actions_taken,
            "actions_recommended": recommendations,
        }
