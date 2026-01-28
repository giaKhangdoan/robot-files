# filename: isaac_fr5_listener.py
from omni.isaac.kit import SimulationApp

# 1. Start Simulator
# We trust the default config. If run from the correct folder, this works automatically.
simulation_app = SimulationApp({"headless": False})

import omni.isaac.core.utils.prims as prim_utils
from omni.isaac.core.world import World
from omni.isaac.core.articulations import Articulation
import redis
import json
import numpy as np
import datetime

# --- CONFIGURATION ---
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
CHANNEL_NAME = 'isaac_feed'
ROBOT_PRIM_PATH = "/World/fairino5_v6_robot" 

def main():
    world = World()
    world.scene.add_default_ground_plane()

    # Setup Robot
    if not prim_utils.is_prim_path_valid(ROBOT_PRIM_PATH):
        print(f"\n❌ ERROR: Robot not found at '{ROBOT_PRIM_PATH}'")
        simulation_app.close()
        return

    fr5_robot = Articulation(prim_path=ROBOT_PRIM_PATH, name="fr5_cobot")
    world.scene.add(fr5_robot)

    # Connect to Redis
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        pubsub = r.pubsub()
        pubsub.subscribe(CHANNEL_NAME)
        print(f"✅ Connected to Redis. Listening on '{CHANNEL_NAME}'")
    except Exception as e:
        print(f"❌ Redis Connection Error: {e}")
        simulation_app.close()
        return

    world.reset()
    fr5_robot.initialize()
    print("🚀 Simulation Started.")

    while simulation_app.is_running():
        world.step(render=True)
        msg = pubsub.get_message(ignore_subscribe_messages=True)
        if msg and msg['type'] == 'message':
            try:
                data = json.loads(msg['data'])
                joints = data.get('Joints', [])
                
                if joints and len(joints) == fr5_robot.num_dof:
                    fr5_robot.set_joint_positions(np.array(joints, dtype=np.float32))
            except Exception:
                pass

    simulation_app.close()

if __name__ == "__main__":
    main()
