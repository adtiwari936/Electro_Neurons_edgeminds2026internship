import argparse
from agent import run_agent

def main():
    parser = argparse.ArgumentParser(
        description="Autonomous Local Research Agent"
    )
    parser.add_argument(
        "topic",
        help="Research topic"
    )

    args = parser.parse_args()

    result = run_agent(args.topic)

    print(result["report"])

if __name__ == "__main__":
    main()