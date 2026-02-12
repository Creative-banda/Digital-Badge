#!/usr/bin/python3
# -*- coding: UTF-8 -*-
"""
Display benchmark test - measures raw LCD refresh rate
Run this on Raspberry Pi to test display performance
"""

import sys
import os
import time
from PIL import Image
import glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import LCD_1inch28

LCD_SIZE = 240

def benchmark_display():
    print("=== LCD Display Benchmark ===")
    
    # Initialize display
    print("Initializing display...")
    disp = LCD_1inch28.LCD_1inch28()
    disp.Init()
    disp.clear()
    disp.bl_DutyCycle(50)
    print("✓ Display initialized\n")
    
    # Test 1: Solid color frames
    print("Test 1: Solid color animation (100 frames)")
    colors = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green
        (0, 0, 255),    # Blue
        (255, 255, 0),  # Yellow
        (255, 0, 255),  # Magenta
    ]
    
    frames = []
    for color in colors:
        img = Image.new("RGB", (LCD_SIZE, LCD_SIZE), color)
        frames.append(img)
    
    start = time.time()
    for i in range(100):
        disp.ShowImage(frames[i % len(frames)])
    elapsed = time.time() - start
    fps = 100 / elapsed
    print(f"  Time: {elapsed:.2f}s")
    print(f"  FPS: {fps:.1f}\n")
    
    # Test 2: Pre-loaded animation frames
    print("Test 2: Real animation frames (idle)")
    idle_frames = []
    frame_files = sorted(glob.glob("animations/idle/*.jpg"))
    
    if frame_files:
        print(f"  Loading {len(frame_files)} frames...")
        for frame_file in frame_files:
            img = Image.open(frame_file).convert("RGB")
            img = img.resize((LCD_SIZE, LCD_SIZE), Image.LANCZOS)
            img = img.rotate(180)  # Pre-rotate
            idle_frames.append(img)
        
        print(f"  Playing animation (2 full loops)...")
        loops = 2
        total_frames = len(idle_frames) * loops
        
        start = time.time()
        for loop in range(loops):
            for frame in idle_frames:
                disp.ShowImage(frame)
        elapsed = time.time() - start
        fps = total_frames / elapsed
        
        print(f"  Frames: {total_frames}")
        print(f"  Time: {elapsed:.2f}s")
        print(f"  FPS: {fps:.1f}\n")
    else:
        print("  No animation frames found!\n")
    
    # Test 3: With rotation (worst case)
    print("Test 3: Animation with runtime rotation (worst case)")
    if idle_frames:
        # Reload without pre-rotation
        test_frames = []
        for frame_file in frame_files[:20]:  # Just use 20 frames
            img = Image.open(frame_file).convert("RGB")
            img = img.resize((LCD_SIZE, LCD_SIZE), Image.LANCZOS)
            # Don't pre-rotate
            test_frames.append(img)
        
        print(f"  Playing {len(test_frames)} frames with rotation...")
        start = time.time()
        for frame in test_frames:
            disp.ShowImage(frame.rotate(180))  # Rotate on each display
        elapsed = time.time() - start
        fps = len(test_frames) / elapsed
        
        print(f"  Time: {elapsed:.2f}s")
        print(f"  FPS: {fps:.1f}\n")
    
    # Cleanup
    disp.module_exit()
    
    print("=== Benchmark Complete ===")
    print("\nExpected Results:")
    print("  Good: 15-30 FPS (Raspberry Pi 3/4)")
    print("  Excellent: 30+ FPS (Raspberry Pi 4/5)")
    print("\nIf FPS < 10:")
    print("  - Check SPI speed in lcdconfig.py (should be 40MHz)")
    print("  - Ensure you're using hardware SPI (not bit-bang)")
    print("  - Pre-rotate all images during load (don't rotate on display)")

if __name__ == "__main__":
    try:
        benchmark_display()
    except KeyboardInterrupt:
        print("\nBenchmark cancelled")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
