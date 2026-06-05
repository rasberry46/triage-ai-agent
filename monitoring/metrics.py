"""
CloudWatch + MLflow metrics tracker.
Tracks triage cycle time, routing accuracy, confidence scores.
"""
import boto3
import logging
from datetime import datetime
from config.settings import settings

logger = logging.getLogger(__name__)


class MetricsTracker:

    @staticmethod
    def record_triage(result: dict):
        logger.info(f"[METRICS] ticket={result.get('ticket_id')} "
                    f"priority={result.get('priority')} "
                    f"team={result.get('assigned_team')} "
                    f"confidence={result.get('confidence_score'):.2f}")

    @staticmethod
    def push_cloudwatch(result: dict):
        try:
            cw = boto3.client("cloudwatch", region_name=settings.AWS_REGION)
            cw.put_metric_data(
                Namespace="TriageAI",
                MetricData=[
                    {"MetricName": "ConfidenceScore",
                     "Value": result.get("confidence_score", 0),
                     "Unit": "None",
                     "Dimensions": [{"Name": "Team", "Value": result.get("assigned_team", "unknown")}]},
                    {"MetricName": "TriageCompleted",
                     "Value": 1, "Unit": "Count"},
                ]
            )
        except Exception as e:
            logger.warning(f"CloudWatch push failed: {e}")

    @staticmethod
    def record_failure(ticket_id: str, error: str):
        logger.error(f"[FAILURE] ticket={ticket_id} error={error}")
