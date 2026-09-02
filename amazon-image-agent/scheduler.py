"""
Windows Task Scheduler setup for Amazon Image Agent
Creates a scheduled task to run the agent daily
"""
import subprocess
import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent
AGENT_SCRIPT = PROJECT_ROOT / "agent.py"
PYTHON_EXE = sys.executable


def create_scheduled_task(
    task_name: str = "AmazonImageAgent",
    run_time: str = "09:00",  # 9 AM daily
    description: str = "Amazon Image Agent - Automated product image generation"
) -> bool:
    """
    Create a Windows scheduled task to run the agent daily
    
    Args:
        task_name: Name of the scheduled task
        run_time: Time to run (HH:MM format, 24-hour)
        description: Task description
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Build the schtasks command
        # /SC DAILY = run daily
        # /TN = task name
        # /TR = task to run (python agent.py)
        # /ST = start time
        # /F = force create (overwrite if exists)
        
        command = [
            "schtasks",
            "/Create",
            "/SC", "DAILY",
            "/TN", task_name,
            "/TR", f'"{PYTHON_EXE}" "{AGENT_SCRIPT}"',
            "/ST", run_time,
            "/F",  # Force overwrite if exists
            "/RL", "HIGHEST",  # Run with highest privileges
            "/RU", "SYSTEM"  # Run as SYSTEM user
        ]
        
        logger.info(f"Creating scheduled task: {task_name}")
        logger.info(f"Will run daily at {run_time}")
        logger.info(f"Command: {' '.join(command)}")
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info(f"Task created successfully: {result.stdout}")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create scheduled task: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error creating scheduled task: {str(e)}")
        return False


def delete_scheduled_task(task_name: str = "AmazonImageAgent") -> bool:
    """
    Delete the scheduled task
    
    Args:
        task_name: Name of the scheduled task
    
    Returns:
        True if successful, False otherwise
    """
    try:
        command = ["schtasks", "/Delete", "/TN", task_name, "/F"]
        
        logger.info(f"Deleting scheduled task: {task_name}")
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info(f"Task deleted successfully: {result.stdout}")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to delete scheduled task: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error deleting scheduled task: {str(e)}")
        return False


def check_task_status(task_name: str = "AmazonImageAgent") -> None:
    """
    Check the status of the scheduled task
    
    Args:
        task_name: Name of the scheduled task
    """
    try:
        command = ["schtasks", "/Query", "/TN", task_name, "/V", "/FO", "LIST"]
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        
        print(result.stdout)
        
    except subprocess.CalledProcessError as e:
        print(f"Task not found or error: {e.stderr}")
    except Exception as e:
        print(f"Error checking task status: {str(e)}")


def run_task_now(task_name: str = "AmazonImageAgent") -> bool:
    """
    Run the scheduled task immediately (for testing)
    
    Args:
        task_name: Name of the scheduled task
    
    Returns:
        True if successful, False otherwise
    """
    try:
        command = ["schtasks", "/Run", "/TN", task_name]
        
        logger.info(f"Running task immediately: {task_name}")
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info(f"Task started: {result.stdout}")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run task: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error running task: {str(e)}")
        return False


def main():
    """Main entry point for scheduler setup"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage Amazon Image Agent scheduled task")
    parser.add_argument(
        "action",
        choices=["create", "delete", "status", "run"],
        help="Action to perform"
    )
    parser.add_argument(
        "--time",
        default="09:00",
        help="Time to run daily (HH:MM, 24-hour format). Default: 09:00"
    )
    parser.add_argument(
        "--name",
        default="AmazonImageAgent",
        help="Task name. Default: AmazonImageAgent"
    )
    
    args = parser.parse_args()
    
    if args.action == "create":
        success = create_scheduled_task(
            task_name=args.name,
            run_time=args.time
        )
        if success:
            print(f"✓ Scheduled task '{args.name}' created successfully")
            print(f"  Will run daily at {args.time}")
            print(f"\nTo check status: python scheduler.py status")
            print(f"To run now: python scheduler.py run")
        else:
            print("✗ Failed to create scheduled task")
            sys.exit(1)
    
    elif args.action == "delete":
        success = delete_scheduled_task(task_name=args.name)
        if success:
            print(f"✓ Scheduled task '{args.name}' deleted successfully")
        else:
            print("✗ Failed to delete scheduled task")
            sys.exit(1)
    
    elif args.action == "status":
        check_task_status(task_name=args.name)
    
    elif args.action == "run":
        success = run_task_now(task_name=args.name)
        if success:
            print(f"✓ Task '{args.name}' started")
            print(f"  Check logs at: {PROJECT_ROOT / 'logs' / 'agent.log'}")
        else:
            print("✗ Failed to run task")
            sys.exit(1)


if __name__ == "__main__":
    main()
