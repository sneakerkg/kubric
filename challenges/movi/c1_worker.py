# Copyright 2022 The Kubric Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Worker file for the Memory cirriculum 1.
Objects:
  * The number of objects is randomly chosen between
    --min_num_objects (3) and --max_num_objects (10)
  * The objects are randomly chosen from either the CLEVR (MOVi-A) or the
    KuBasic set.
  * They are either rubber or metallic with different different colors and sizes


C1
  --camera=clevr --background=clevr --objects_set=clevr
  --min_num_objects=3 --max_num_objects=5

"""

import logging

import sys
sys.path.append("/kubric")

import kubric as kb
from kubric.simulator import PyBullet
from kubric.renderer import Blender
import numpy as np

# --- Some configuration values
# the region in which to place objects [(min), (max)]
SPAWN_REGION = [(-3, -3, 0), (3, 3, 1)]
VELOCITY_RANGE = [(-4., -4., 0.), (4., 4., 0.)]
#CLEVR_OBJECTS = ("cube", "cylinder", "sphere")
# Cube sometimes fails to place if SPAWN_REGION is with max z 0
CLEVR_OBJECTS = ("cylinder", "sphere")
KUBASIC_OBJECTS = ("cube", "cylinder", "sphere", "cone", "torus", "gear",
                   "torus_knot", "sponge", "spot", "teapot", "suzanne")

# --- CLI arguments
parser = kb.ArgumentParser()
# Configuration for the objects of the scene
parser.add_argument("--objects_set", choices=["clevr", "kubasic"],
                    default="clevr")
parser.add_argument("--min_num_objects", type=int, default=5,
                    help="minimum number of objects")
parser.add_argument("--max_num_objects", type=int, default=5,
                    help="maximum number of objects")
# Configuration for the floor and background
parser.add_argument("--floor_friction", type=float, default=0.0)
parser.add_argument("--floor_restitution", type=float, default=0.5)
parser.add_argument("--job_dir", type=str, default=".")
parser.add_argument("--background", choices=["clevr", "colored"],
                    default="clevr")

# Configuration for the camera
parser.add_argument("--camera", choices=["clevr", "random"], default="clevr")
parser.add_argument("--motion", choices=["parallel", "random"], default="parallel")

# Configuration for the source of the assets
parser.add_argument("--kubasic_assets", type=str,
                    default="gs://kubric-public/assets/KuBasic/KuBasic.json")
parser.add_argument("--save_state", dest="save_state", action="store_true")
parser.set_defaults(save_state=False, frame_end=24, frame_rate=12,
                    resolution=64)
FLAGS = parser.parse_args()

# --- Common setups & resources
scene, rng, output_dir, scratch_dir = kb.setup(FLAGS)
simulator = PyBullet(scene, scratch_dir)
renderer = Blender(scene, scratch_dir, samples_per_pixel=64)
kubasic = kb.AssetSource.from_manifest(FLAGS.kubasic_assets)


# --- Populate the scene
# Floor / Background
logging.info("Creating a large gray floor...")
floor_material = kb.PrincipledBSDFMaterial(roughness=1., specular=0.)
scene += kubasic.create("dome", name="floor", material=floor_material,
                        scale=2.0,
                        friction=FLAGS.floor_friction,
                        restitution=FLAGS.floor_restitution,
                        static=True, background=True)
if FLAGS.background == "clevr":
  floor_material.color = kb.Color.from_name("gray")
  scene.metadata["background"] = "clevr"
elif FLAGS.background == "colored":
  floor_material.color = kb.random_hue_color()
  scene.metadata["background"] = floor_material.color.hexstr


wall_material = kb.FlatMaterial(color=kb.get_color('white'),
                                indirect_visibility=False)

# Add walls
north_wall = kb.Cube(scale=(6, 0.1, 3), position=(0, -5.5, 0),
                     material=wall_material, static=True, background=True,
                     restitution=1., friction=0.)
south_wall = kb.Cube(scale=(6, 0.1, 3), position=(0, 5.5, 0),
                     material=wall_material, static=True, background=True,
                     restitution=1., friction=0.)
east_wall = kb.Cube(scale=(0.1, 6, 3), position=(-5.5, 0, 0),
                     material=wall_material, static=True, background=True,
                     restitution=1., friction=0.)
west_wall = kb.Cube(scale=(0.1, 6, 3), position=(5.5, 0, 0),
                     material=wall_material, static=True, background=True,
                     restitution=1., friction=0.)                     

scene.add([north_wall, south_wall, east_wall, west_wall])


# Lights
logging.info("Adding four (studio) lights to the scene similar to CLEVR...")
scene.add(kb.assets.utils.get_clevr_lights(rng=rng))
scene.ambient_illumination = kb.Color(0.05, 0.05, 0.05)

# Camera
logging.info("Setting up the Camera...")
scene.camera = kb.PerspectiveCamera(focal_length=35., sensor_width=32)
if FLAGS.camera == "clevr":  # Specific position + jitter
  scene.camera.position = [0, 0, 12]
if FLAGS.camera == "random":  # Random position in half-sphere-shell
  scene.camera.position = kb.sample_point_in_half_sphere_shell(
      inner_radius=7., outer_radius=9., offset=0.1)
scene.camera.look_at((0, 0, 0))
print (scene.camera.position)


# Add random objects
num_objects = rng.randint(FLAGS.min_num_objects,
                          FLAGS.max_num_objects+1)
logging.info("Randomly placing %d objects:", num_objects)

catched_motion = None
for i in range(num_objects):
  if FLAGS.objects_set == "clevr":
    shape_name = rng.choice(CLEVR_OBJECTS)
    size_label, size = kb.randomness.sample_sizes("clevr", rng)
    color_label, random_color = kb.randomness.sample_color("clevr", rng)
  else:  # FLAGS.object_set == "kubasic":
    shape_name = rng.choice(KUBASIC_OBJECTS)
    size_label, size = kb.randomness.sample_sizes("uniform", rng)
    color_label, random_color = kb.randomness.sample_color("uniform_hue", rng)

  material_name = rng.choice(["metal", "rubber"])
  obj = kubasic.create(
      asset_id=shape_name, scale=size,
      name=f"{size_label} {color_label} {material_name} {shape_name}")
  assert isinstance(obj, kb.FileBasedObject)

  if material_name == "metal":
    obj.material = kb.PrincipledBSDFMaterial(color=random_color, metallic=1.0,
                                             roughness=0.2, ior=2.5)
    obj.friction = 0.4
    obj.restitution = 0.3
    obj.mass *= 2.7 * size**3
  else:  # material_name == "rubber"
    obj.material = kb.PrincipledBSDFMaterial(color=random_color, metallic=0.,
                                             ior=1.25, roughness=0.7,
                                             specular=0.33)
    obj.friction = 0.8
    obj.restitution = 0.7
    obj.mass *= 1.1 * size**3

  obj.metadata = {
      "shape": shape_name.lower(),
      "size": size,
      "size_label": size_label,
      "material": material_name.lower(),
      "color": random_color.rgb,
      "color_label": color_label,
  }
  scene.add(obj)
  kb.move_until_no_overlap(obj, simulator, spawn_region=SPAWN_REGION, rng=rng)
  
  '''
  # initialize velocity randomly but biased towards center
  obj.velocity = (rng.uniform(*VELOCITY_RANGE) -
                  [obj.position[0], obj.position[1], 0])
  '''
  obj.velocity = rng.uniform(*VELOCITY_RANGE)
  if catched_motion is None:
    catched_motion = obj.velocity
  
  if FLAGS.motion == "parallel":
    obj.velocity = (2* rng.randint(0, 2) - 1) * catched_motion


  logging.info("    Added %s at %s", obj.asset_id, obj.position)


if FLAGS.save_state:
  logging.info("Saving the simulator state to '%s' prior to the simulation.",
               output_dir / "scene.bullet")
  simulator.save_state(output_dir / "scene.bullet")

# Run dynamic objects simulation
logging.info("Running the simulation ...")
animation, collisions = simulator.run(frame_start=0,
                                      frame_end=scene.frame_end+1)

# --- Rendering
if FLAGS.save_state:
  logging.info("Saving the renderer state to '%s' ",
               output_dir / "scene.blend")
  renderer.save_state(output_dir / "scene.blend")


logging.info("Rendering the scene ...")
data_stack = renderer.render()

# --- Postprocessing
kb.compute_visibility(data_stack["segmentation"], scene.assets)
visible_foreground_assets = [asset for asset in scene.foreground_assets
                             if np.max(asset.metadata["visibility"]) > 0]
visible_foreground_assets = sorted(  # sort assets by their visibility
    visible_foreground_assets,
    key=lambda asset: np.sum(asset.metadata["visibility"]),
    reverse=True)

data_stack["segmentation"] = kb.adjust_segmentation_idxs(
    data_stack["segmentation"],
    scene.assets,
    visible_foreground_assets)
scene.metadata["num_instances"] = len(visible_foreground_assets)

# Save to image files
kb.write_image_dict(data_stack, output_dir)
kb.post_processing.compute_bboxes(data_stack["segmentation"],
                                  visible_foreground_assets)

# --- Metadata
logging.info("Collecting and storing metadata for each object.")
kb.write_json(filename=output_dir / "metadata.json", data={
    "flags": vars(FLAGS),
    "metadata": kb.get_scene_metadata(scene),
    "camera": kb.get_camera_info(scene.camera),
    "instances": kb.get_instance_info(scene, visible_foreground_assets),
})
kb.write_json(filename=output_dir / "events.json", data={
    "collisions":  kb.process_collisions(
        collisions, scene, assets_subset=visible_foreground_assets),
})

kb.done()
