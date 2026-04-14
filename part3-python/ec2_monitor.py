import boto3
import argparse
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any

from botocore.exceptions import BotoCoreError, ClientError


# ---------------- Logging Setup ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# ---------------- Helpers ----------------
def load_config(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config file: {e}")
        return {}


def get_ec2_instances(ec2_client) -> List[Dict[str, Any]]:
    try:
        response = ec2_client.describe_instances(
            Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
        )

        instances = []
        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                name = ""
                for tag in instance.get("Tags", []):
                    if tag["Key"] == "Name":
                        name = tag["Value"]

                instances.append({
                    "InstanceId": instance["InstanceId"],
                    "Name": name,
                    "Type": instance["InstanceType"]
                })

        return instances

    except (BotoCoreError, ClientError) as e:
        logger.error(f"Error fetching EC2 instances: {e}")
        return []


def get_cpu_metrics(cloudwatch, instance_id: str) -> Dict[str, float]:
    try:
        end = datetime.now(timezone.utc)
        start = end - timedelta(hours=1)

        metrics = cloudwatch.get_metric_statistics(
            Namespace="AWS/EC2",
            MetricName="CPUUtilization",
            Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
            StartTime=start,
            EndTime=end,
            Period=300,
            Statistics=["Average", "Minimum", "Maximum"]
        )

        datapoints = metrics.get("Datapoints", [])

        if not datapoints:
            return {"Average": 0.0, "Minimum": 0.0, "Maximum": 0.0}

        avg = sum(dp["Average"] for dp in datapoints) / len(datapoints)
        min_v = min(dp["Minimum"] for dp in datapoints)
        max_v = max(dp["Maximum"] for dp in datapoints)

        return {
            "Average": round(avg, 2),
            "Minimum": round(min_v, 2),
            "Maximum": round(max_v, 2)
        }

    except (BotoCoreError, ClientError) as e:
        logger.error(f"CloudWatch error for {instance_id}: {e}")
        return {"Average": 0.0, "Minimum": 0.0, "Maximum": 0.0}


# ---------------- Main Logic ----------------
def generate_report(region: str, threshold: float, config_path: str) -> List[Dict[str, Any]]:
    ec2 = boto3.client("ec2", region_name=region)
    cloudwatch = boto3.client("cloudwatch", region_name=region)

    config = load_config(config_path)

    instances = get_ec2_instances(ec2)
    report = []

    for inst in instances:
        cpu = get_cpu_metrics(cloudwatch, inst["InstanceId"])

        flagged = cpu["Average"] > threshold

        report.append({
            "InstanceId": inst["InstanceId"],
            "Name": inst["Name"],
            "Type": inst["Type"],
            "CPU": cpu,
            "Flagged": flagged
        })

    return report


def save_report(data: List[Dict[str, Any]], output: str):
    try:
        with open(output, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Report saved to {output}")
    except Exception as e:
        logger.error(f"Failed to write report: {e}")


# ---------------- CLI ----------------
def main():
    parser = argparse.ArgumentParser(description="EC2 Monitoring Script")

    parser.add_argument("--region", required=True)
    parser.add_argument("--threshold", type=float, default=80)
    parser.add_argument("--output", required=True)
    parser.add_argument("--config", default="config.json")

    args = parser.parse_args()

    try:
        report = generate_report(args.region, args.threshold, args.config)
        save_report(report, args.output)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()