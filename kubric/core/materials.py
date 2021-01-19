# Copyright 2020 The Kubric Authors
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

import traitlets as tl

import kubric.core.traits as ktl
from kubric.core import base
from kubric import core

__all__ = ("Material", "UndefinedMaterial", "PrincipledBSDFMaterial", "FlatMaterial")


class Material(base.Asset):
  """Base class for all materials."""
  pass


class UndefinedMaterial(Material, base.Undefined):
  """Marker class to indicate that Kubric should not interfere with this material."""
  pass


class PrincipledBSDFMaterial(Material):
  """A physically based material suited for uniform colored plastic, rubber, metal, glass, etc..."""
  color = ktl.RGBA(default_value=core.color.get_color("white"))
  metallic = tl.Float(0.)
  specular = tl.Float(0.5)
  specular_tint = tl.Float(0.)
  roughness = tl.Float(0.4)
  ior = tl.Float(1.45)
  transmission = tl.Float(0)
  transmission_roughness = tl.Float(0)
  emission = ktl.RGBA(default_value=core.color.get_color("black"))


class FlatMaterial(Material):
  """Renders the object as a uniform color without any shading.
  If holdout is true, then the pixels of the object will be transparent in the final image (alpha=0).
  (Note, that this is not the same as a transparent object. It still "occludes" other objects)

  The indirect_visibility flag controls if the object casts shadows, can be seen in reflections and
  emits light.
  """
  color = ktl.RGBA(default_value=core.color.get_color("white"))
  holdout = tl.Bool(False)
  indirect_visibility = tl.Bool(True)