import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

SDK_ROOT = REPO_ROOT / "unitree_sdk2_python"
if str(SDK_ROOT) not in sys.path:
    sys.path.insert(0, str(SDK_ROOT))

from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.comm.motion_switcher.motion_switcher_client import MotionSwitcherClient
from unitree_sdk2py.g1.arm.g1_arm_action_api import (
    ARM_ACTION_SERVICE_NAME,
    ARM_ACTION_API_VERSION,
    ROBOT_API_ID_ARM_ACTION_GET_ACTION_LIST,
)
from unitree_sdk2py.g1.arm.g1_arm_action_client import G1ArmActionClient
from unitree_sdk2py.g1.loco.g1_loco_api import (
    LOCO_SERVICE_NAME,
    LOCO_API_VERSION,
    ROBOT_API_ID_LOCO_GET_BALANCE_MODE,
    ROBOT_API_ID_LOCO_GET_FSM_ID,
    ROBOT_API_ID_LOCO_GET_FSM_MODE,
    ROBOT_API_ID_LOCO_SET_ARM_TASK,
)
from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient


def print_header(title: str):
    print()
    print("=" * 16, title, "=" * 16)


def probe_motion_switcher():
    print_header("motion_switcher")
    client = MotionSwitcherClient()
    client.SetTimeout(3.0)
    client.Init()
    code, api_version = client.GetServerApiVersion()
    print(f"service=motion_switcher get_server_api_version code={code} api_version={api_version}")
    code, result = client.CheckMode()
    print(f"service=motion_switcher check_mode code={code} result={result}")


def probe_arm_service():
    print_header("arm service")
    client = G1ArmActionClient()
    client.SetTimeout(3.0)
    client.Init()
    print(f"service={ARM_ACTION_SERVICE_NAME} sdk_api_version={ARM_ACTION_API_VERSION}")

    code, api_version = client.GetServerApiVersion()
    print(f"service={ARM_ACTION_SERVICE_NAME} get_server_api_version code={code} api_version={api_version}")

    code, action_list = client.GetActionList()
    print(
        f"service={ARM_ACTION_SERVICE_NAME} api_id={ROBOT_API_ID_ARM_ACTION_GET_ACTION_LIST} "
        f"get_action_list code={code} action_list={action_list}"
    )


def probe_sport_service(set_arm_task_id=None):
    print_header("sport service")
    client = LocoClient()
    client.SetTimeout(3.0)
    client.Init()
    print(f"service={LOCO_SERVICE_NAME} sdk_api_version={LOCO_API_VERSION}")

    code, api_version = client.GetServerApiVersion()
    print(f"service={LOCO_SERVICE_NAME} get_server_api_version code={code} api_version={api_version}")

    for api_id, label in [
        (ROBOT_API_ID_LOCO_GET_FSM_ID, "get_fsm_id"),
        (ROBOT_API_ID_LOCO_GET_FSM_MODE, "get_fsm_mode"),
        (ROBOT_API_ID_LOCO_GET_BALANCE_MODE, "get_balance_mode"),
    ]:
        code, data = client._Call(api_id, "{}")
        print(f"service={LOCO_SERVICE_NAME} api_id={api_id} {label} code={code} data={data}")

    if set_arm_task_id is not None:
        code = client.SetTaskId(set_arm_task_id)
        print(
            f"service={LOCO_SERVICE_NAME} api_id={ROBOT_API_ID_LOCO_SET_ARM_TASK} "
            f"set_arm_task task_id={set_arm_task_id} code={code}"
        )


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--network-interface", default="eno1")
    parser.add_argument(
        "--sport-task-id",
        type=int,
        default=None,
        help="Optional: actively call sport.SetTaskId(task_id). This may trigger arm motions.",
    )
    args = parser.parse_args()

    print(f"sdk_root={SDK_ROOT}")
    print(f"imported_unitree_sdk2py={Path(sys.modules['unitree_sdk2py'].__file__).resolve()}")
    print(f"network_interface={args.network_interface}")

    ChannelFactoryInitialize(0, networkInterface=args.network_interface)

    probe_motion_switcher()
    probe_arm_service()
    probe_sport_service(set_arm_task_id=args.sport_task_id)


if __name__ == "__main__":
    main()
