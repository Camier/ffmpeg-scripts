#!/usr/bin/env python3
"""
Motion Vector Figure Art Generator
Creates artistic visualizations using motion vectors to form figure shapes.
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch, Circle, Polygon
import os
from pathlib import Path
import random
import glob
from typing import List, Tuple
import time

class MotionVectorFigureArt:
    """Generate figure-shaped art using motion vector data."""
    
    def __init__(self):
        self.output_dir = Path("/home/mik/VECTOR/motion_vector_figure_art")
        self.output_dir.mkdir(exist_ok=True)
        
        # Figure art styles
        self.vector_styles = {
            'arrow_silhouette': {
                'colors': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'],
                'arrow_scale': 2.0,
                'arrow_width': 2,
                'density': 10
            },
            'flow_figure': {
                'colors': ['#9B59B6', '#3498DB', '#E74C3C', '#F39C12', '#2ECC71'],
                'line_width': 3,
                'alpha': 0.8,
                'density': 8
            },
            'vector_sculpture': {
                'colors': ['#34495E', '#E67E22', '#1ABC9C', '#E91E63', '#9C27B0'],
                'vector_length': 25,
                'thickness': 2.5,
                'density': 12
            }
        }
    
    def get_all_frame_paths(self) -> List[str]:
        """Get all motion vector frame paths."""
        frame_paths = []
        
        art_dirs = [
            "/home/mik/VECTOR/motion_vector_art/ba_art/frames",
            "/home/mik/VECTOR/motion_vector_art/ballerina_archive_art/frames", 
            "/home/mik/VECTOR/motion_vector_art/istock_ballet_1_art/frames",
            "/home/mik/VECTOR/motion_vector_art/istock_ballet_2_art/frames",
            "/home/mik/VECTOR/motion_vector_art/istock_ballet_3_art/frames"
        ]
        
        for art_dir in art_dirs:
            if os.path.exists(art_dir):
                pattern = os.path.join(art_dir, "*.png")
                frames = glob.glob(pattern)
                frame_paths.extend(frames)
        
        return sorted(frame_paths)
    
    def extract_motion_vectors_from_ffmpeg_frame(self, frame_path: str) -> List[Tuple]:
        """Extract motion vectors from FFmpeg codecview frame."""
        frame = cv2.imread(frame_path)
        if frame is None:
            return []
        
        h, w = frame.shape[:2]
        
        # Convert to HSV to isolate green motion vectors
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Create mask for green arrows (FFmpeg motion vectors)
        lower_green = np.array([40, 50, 50])
        upper_green = np.array([80, 255, 255])
        green_mask = cv2.inRange(hsv, lower_green, upper_green)
        
        # Find contours of motion vector arrows
        contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        motion_vectors = []
        
        for contour in contours:
            if cv2.contourArea(contour) > 8:  # Filter noise
                # Get oriented bounding box
                if len(contour) >= 5:
                    ellipse = cv2.fitEllipse(contour)
                    (cx, cy), (width, height), angle = ellipse
                    
                    # Convert angle to radians
                    angle_rad = np.radians(angle)
                    
                    # Calculate vector direction and magnitude
                    vector_length = max(width, height) / 2
                    dx = vector_length * np.cos(angle_rad)
                    dy = vector_length * np.sin(angle_rad)
                    
                    motion_vectors.append((int(cx), int(cy), dx, dy, vector_length))
        
        return motion_vectors
    
    def detect_figure_silhouette(self, frame_path: str) -> dict:
        """Detect dancer silhouette for figure shaping."""
        frame = cv2.imread(frame_path)
        if frame is None:
            return {}
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Create silhouette mask
        _, binary = cv2.threshold(gray, 90, 255, cv2.THRESH_BINARY_INV)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return {}
        
        # Get the largest contour (dancer)
        main_contour = max(contours, key=cv2.contourArea)
        
        # Calculate characteristics
        moments = cv2.moments(main_contour)
        if moments['m00'] == 0:
            return {}
        
        cx = int(moments['m10'] / moments['m00'])
        cy = int(moments['m01'] / moments['m00'])
        
        # Simplify contour for artistic representation
        epsilon = 0.005 * cv2.arcLength(main_contour, True)
        simplified_contour = cv2.approxPolyDP(main_contour, epsilon, True)
        
        return {
            'center': (cx, cy),
            'contour': main_contour,
            'simplified_contour': simplified_contour,
            'area': cv2.contourArea(main_contour)
        }
    
    def create_arrow_silhouette_art(self, frame_path: str, frame_name: str):
        """Create figure art using motion vector arrows."""
        motion_vectors = self.extract_motion_vectors_from_ffmpeg_frame(frame_path)
        figure_data = self.detect_figure_silhouette(frame_path)
        
        if not motion_vectors or not figure_data:
            return None
        
        frame = cv2.imread(frame_path)
        h, w = frame.shape[:2]
        
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.set_xlim(0, w)
        ax.set_ylim(h, 0)
        ax.set_aspect('equal')
        ax.set_facecolor('black')
        
        style = self.vector_styles['arrow_silhouette']
        colors = style['colors']
        
        # Draw motion vector arrows forming figure shape
        for i, (x, y, dx, dy, magnitude) in enumerate(motion_vectors):
            if magnitude > 3:  # Only significant vectors
                # Scale arrow
                arrow_dx = dx * style['arrow_scale']
                arrow_dy = dy * style['arrow_scale']
                
                # Create arrow
                arrow = FancyArrowPatch(
                    (x, y), (x + arrow_dx, y + arrow_dy),
                    arrowstyle='->', 
                    mutation_scale=magnitude * 2,
                    color=colors[i % len(colors)],
                    alpha=0.8,
                    linewidth=style['arrow_width']
                )
                ax.add_patch(arrow)
        
        # Add figure outline in contrasting color
        if 'simplified_contour' in figure_data:
            contour_points = figure_data['simplified_contour'].reshape(-1, 2)
            polygon = Polygon(contour_points, fill=False, edgecolor='white', 
                            linewidth=2, alpha=0.6)
            ax.add_patch(polygon)
        
        ax.set_title(f'Arrow Silhouette: {frame_name}', 
                    color='white', fontsize=14, fontweight='bold')
        ax.axis('off')
        
        output_path = self.output_dir / f"{frame_name}_arrow_silhouette.png"
        plt.tight_layout()
        plt.savefig(output_path, dpi=200, bbox_inches='tight', 
                   facecolor='black', edgecolor='none')
        plt.close()
        
        return str(output_path)
    
    def create_flow_figure_art(self, frame_path: str, frame_name: str):
        """Create flowing figure art using motion vectors."""
        motion_vectors = self.extract_motion_vectors_from_ffmpeg_frame(frame_path)
        figure_data = self.detect_figure_silhouette(frame_path)
        
        if not motion_vectors or not figure_data:
            return None
        
        frame = cv2.imread(frame_path)
        h, w = frame.shape[:2]
        
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.set_xlim(0, w)
        ax.set_ylim(h, 0)
        ax.set_aspect('equal')
        
        # Gradient background
        gradient = np.linspace(0, 1, w).reshape(1, -1)
        gradient = np.vstack([gradient] * h)
        ax.imshow(gradient, extent=[0, w, h, 0], cmap='plasma', alpha=0.3)
        
        style = self.vector_styles['flow_figure']
        colors = style['colors']
        
        # Create flowing lines following motion vectors
        center = figure_data['center']
        cx, cy = center
        
        for i, (x, y, dx, dy, magnitude) in enumerate(motion_vectors):
            if magnitude > 2:
                # Create flowing curve
                curve_points = []
                steps = 15
                
                for step in range(steps):
                    t = step / steps
                    
                    # Calculate flowing curve
                    curve_x = x + dx * t * 2 + 10 * np.sin(t * np.pi * 3)
                    curve_y = y + dy * t * 2 + 5 * np.cos(t * np.pi * 2)
                    
                    curve_points.append([curve_x, curve_y])
                
                # Draw flowing line
                curve_points = np.array(curve_points)
                if len(curve_points) > 1:
                    for j in range(len(curve_points) - 1):
                        alpha = style['alpha'] * (1 - j / len(curve_points))
                        ax.plot([curve_points[j, 0], curve_points[j+1, 0]], 
                               [curve_points[j, 1], curve_points[j+1, 1]], 
                               color=colors[i % len(colors)], 
                               alpha=alpha, linewidth=style['line_width'])
        
        # Add figure outline
        if 'contour' in figure_data:
            contour = figure_data['contour']
            contour_points = contour.reshape(-1, 2)
            ax.plot(contour_points[:, 0], contour_points[:, 1], 
                   color='white', linewidth=2, alpha=0.7)
        
        ax.set_title(f'Flow Figure: {frame_name}', 
                    color='#9B59B6', fontsize=14, fontweight='bold')
        ax.axis('off')
        
        output_path = self.output_dir / f"{frame_name}_flow_figure.png"
        plt.tight_layout()
        plt.savefig(output_path, dpi=200, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        
        return str(output_path)
    
    def create_vector_sculpture_art(self, frame_path: str, frame_name: str):
        """Create sculptural figure art using motion vectors."""
        motion_vectors = self.extract_motion_vectors_from_ffmpeg_frame(frame_path)
        figure_data = self.detect_figure_silhouette(frame_path)
        
        if not motion_vectors or not figure_data:
            return None
        
        frame = cv2.imread(frame_path)
        h, w = frame.shape[:2]
        
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.set_xlim(0, w)
        ax.set_ylim(h, 0)
        ax.set_aspect('equal')
        ax.set_facecolor('#F8F9FA')
        
        style = self.vector_styles['vector_sculpture']
        colors = style['colors']
        
        # Create sculptural vectors
        for i, (x, y, dx, dy, magnitude) in enumerate(motion_vectors):
            if magnitude > 1:
                # Create thick vector lines
                vector_length = style['vector_length']
                end_x = x + (dx / magnitude) * vector_length if magnitude > 0 else x
                end_y = y + (dy / magnitude) * vector_length if magnitude > 0 else y
                
                # Draw thick vector
                ax.plot([x, end_x], [y, end_y], 
                       color=colors[i % len(colors)], 
                       linewidth=style['thickness'], 
                       alpha=0.9,
                       solid_capstyle='round')
                
                # Add vector head
                head_size = magnitude * 2
                circle = Circle((end_x, end_y), head_size, 
                              color=colors[i % len(colors)], alpha=0.8)
                ax.add_patch(circle)
        
        # Add sculptural figure base
        if 'simplified_contour' in figure_data:
            contour_points = figure_data['simplified_contour'].reshape(-1, 2)
            
            # Create shadow effect
            shadow_points = contour_points + [3, 3]  # Offset for shadow
            shadow_polygon = Polygon(shadow_points, fill=True, 
                                   facecolor='gray', alpha=0.3)
            ax.add_patch(shadow_polygon)
            
            # Main figure outline
            polygon = Polygon(contour_points, fill=False, 
                            edgecolor='#2C3E50', linewidth=3, alpha=0.8)
            ax.add_patch(polygon)
        
        ax.set_title(f'Vector Sculpture: {frame_name}', 
                    color='#2C3E50', fontsize=14, fontweight='bold')
        ax.axis('off')
        
        output_path = self.output_dir / f"{frame_name}_vector_sculpture.png"
        plt.tight_layout()
        plt.savefig(output_path, dpi=200, bbox_inches='tight', 
                   facecolor='#F8F9FA', edgecolor='none')
        plt.close()
        
        return str(output_path)
    
    def process_single_frame(self, frame_info: Tuple[str, int, int]) -> List[str]:
        """Process single frame with all figure art styles."""
        frame_path, frame_idx, total_frames = frame_info
        
        frame_name = Path(frame_path).stem
        print(f"Processing [{frame_idx+1}/{total_frames}]: {frame_name}")
        
        created_files = []
        
        # Generate all three figure art styles
        try:
            result = self.create_arrow_silhouette_art(frame_path, frame_name)
            if result:
                created_files.append(result)
        except Exception as e:
            print(f"  ✗ Arrow silhouette failed: {e}")
        
        try:
            result = self.create_flow_figure_art(frame_path, frame_name)
            if result:
                created_files.append(result)
        except Exception as e:
            print(f"  ✗ Flow figure failed: {e}")
        
        try:
            result = self.create_vector_sculpture_art(frame_path, frame_name)
            if result:
                created_files.append(result)
        except Exception as e:
            print(f"  ✗ Vector sculpture failed: {e}")
        
        return created_files
    
    def generate_figure_art_collection(self):
        """Generate motion vector figure art collection."""
        
        frame_paths = self.get_all_frame_paths()
        
        if not frame_paths:
            print("No motion vector frames found!")
            return
        
        print(f"🎨 Motion Vector Figure Art Generator")
        print(f"Found {len(frame_paths)} motion vector frames")
        print(f"Generating 3 figure art styles per frame = {len(frame_paths) * 3} total artworks")
        print(f"Output directory: {self.output_dir}")
        
        frame_infos = [(path, idx, len(frame_paths)) for idx, path in enumerate(frame_paths)]
        
        start_time = time.time()
        all_created_files = []
        
        # Process frames
        for frame_info in frame_infos:
            created_files = self.process_single_frame(frame_info)
            all_created_files.extend(created_files)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Summary
        print("\n" + "="*60)
        print("MOTION VECTOR FIGURE ART COLLECTION COMPLETE")
        print("="*60)
        print(f"Processed frames: {len(frame_paths)}")
        print(f"Created artworks: {len(all_created_files)}")
        print(f"Processing time: {processing_time:.1f} seconds")
        print(f"Average time per frame: {processing_time/len(frame_paths):.1f} seconds")
        print(f"Output location: {self.output_dir}")
        
        # Calculate file sizes
        total_size = 0
        for file_path in all_created_files:
            if os.path.exists(file_path):
                total_size += os.path.getsize(file_path)
        
        total_size_mb = total_size / (1024 * 1024)
        print(f"Total collection size: {total_size_mb:.1f} MB")
        
        return all_created_files


def main():
    """Generate motion vector figure art collection."""
    
    print("🎭 MOTION VECTOR FIGURE ART GENERATOR")
    print("=" * 50)
    
    generator = MotionVectorFigureArt()
    created_files = generator.generate_figure_art_collection()
    
    print(f"\n✨ Motion vector figure art collection complete!")
    print(f"🎨 {len(created_files)} figure-shaped artworks created!")


if __name__ == "__main__":
    main()