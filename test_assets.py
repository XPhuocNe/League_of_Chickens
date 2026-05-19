#!/usr/bin/env python
"""Quick test of asset loading and sprite initialization."""
import sys
sys.path.insert(0, 'src')

try:
    print("🔍 Testing sprite loading...")
    from entities.projectile import _get_proj_sprites
    sprites = _get_proj_sprites()
    
    print("✅ Sprite cache loaded successfully:")
    for key, frames in sprites.items():
        frame_count = len(frames) if frames else 0
        status = "✓" if frames else "✗"
        print(f"  {status} {key:20s} ({frame_count} frames)")
    
    print("\n🔍 Testing imports...")
    from entities.projectile import Projectile, DelayedCircleAttack
    from entities.enemy import Enemy
    from entities.boss import Boss
    print("✅ All entity classes imported successfully")
    
    print("\n🔍 Testing helper functions...")
    from entities.boss import _get_arrow_sprite, _get_explosion_sprite
    print(f"✅ Water arrow sprite: {_get_arrow_sprite('water')}")
    print(f"✅ Fire arrow sprite: {_get_arrow_sprite('fire')}")
    print(f"✅ Water explosion sprite: {_get_explosion_sprite('water')}")
    print(f"✅ Fire explosion sprite: {_get_explosion_sprite('fire')}")
    
    print("\n✅ All tests passed!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
