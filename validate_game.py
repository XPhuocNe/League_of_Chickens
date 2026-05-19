#!/usr/bin/env python
"""Syntax check and quick validation script."""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test all critical imports."""
    print("=" * 60)
    print("TESTING IMPORTS & SYNTAX")
    print("=" * 60)
    
    errors = []
    
    # Test projectile module
    try:
        from entities.projectile import Projectile, DelayedCircleAttack, _get_proj_sprites
        print("✅ entities.projectile imported successfully")
        
        # Test sprite loading
        sprites = _get_proj_sprites()
        for name, frames in sprites.items():
            count = len(frames) if frames else 0
            if frames:
                print(f"   ✓ {name}: {count} frames")
            else:
                print(f"   ✗ {name}: FAILED TO LOAD")
                errors.append(f"Sprite '{name}' failed to load")
    except Exception as e:
        print(f"❌ entities.projectile: {e}")
        errors.append(str(e))

    # Test enemy module
    try:
        from entities.enemy import Enemy
        print("✅ entities.enemy imported successfully")
    except Exception as e:
        print(f"❌ entities.enemy: {e}")
        errors.append(str(e))

    # Test boss module
    try:
        from entities.boss import Boss, _get_arrow_sprite, _get_explosion_sprite
        print("✅ entities.boss imported successfully")
        
        # Test helper functions
        wa = _get_arrow_sprite("water")
        fa = _get_arrow_sprite("fire")
        we = _get_explosion_sprite("water")
        fe = _get_explosion_sprite("fire")
        
        print(f"   ✓ Helper functions working:")
        print(f"     - water arrow: {wa}")
        print(f"     - fire arrow: {fa}")
        print(f"     - water explosion: {we}")
        print(f"     - fire explosion: {fe}")
    except Exception as e:
        print(f"❌ entities.boss: {e}")
        errors.append(str(e))

    # Test constants
    try:
        from constants import *
        print("✅ constants imported successfully")
    except Exception as e:
        print(f"❌ constants: {e}")
        errors.append(str(e))

    # Test game managers
    try:
        from managers.game_managers import GameManager
        print("✅ managers.game_managers imported successfully")
    except Exception as e:
        print(f"❌ managers.game_managers: {e}")
        errors.append(str(e))

    # Test main
    try:
        import main
        print("✅ main imported successfully")
    except Exception as e:
        print(f"❌ main: {e}")
        errors.append(str(e))

    print("\n" + "=" * 60)
    if errors:
        print(f"❌ FAILED - {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        return False
    else:
        print("✅ ALL TESTS PASSED!")
        print("\n🎮 Game is ready to run:")
        print("   Run: python src\\main.py")
        return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
