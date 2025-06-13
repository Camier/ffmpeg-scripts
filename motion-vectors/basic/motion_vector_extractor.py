#!/usr/bin/env python3
"""
Motion Vector Extractor
Extracts motion vectors from the motion_vector_art directory frames and creates artistic visualizations.
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Circle
import os
from pathlib import Path
import glob
from typing import List, Dict, Tuple
import time
import json
import warnings
warnings.filterwarnings('ignore')

# GPU imports
try:
    import torch
    import torch.nn.functional as F
    GPU_AVAILABLE = torch.cuda.is_available()
    if GPU_AVAILABLE:
        device = torch.device('cuda')
        print(f"🚀 GPU enabled: {torch.cuda.get_device_name()}")
    else:
        device = torch.device('cpu')
        print("💻 CPU processing")
except ImportError:
    GPU_AVAILABLE = False
    device = None
    print("⚠️ PyTorch not available")

class MotionVectorExtractor:
    """Extract motion vectors from motion_vector_art frames."""
    
    def __init__(self):
        self.use_gpu = GPU_AVAILABLE
        self.device = device if GPU_AVAILABLE else None
        
        # Optimized extraction parameters
        self.params = {
            'max_vector_length': 18,        # Maximum length for shape preservation
            'optimal_length': 12,           # Target length
            'min_vector_length': 4,         # Minimum visible length
            'ffmpeg_scale': 0.4,           # FFmpeg vector scaling
            'flow_scale': 0.25,            # Optical flow scaling
            'edge_scale': 0.5,             # Edge vector scaling
            'quality_threshold': 0.3,       # Minimum quality
            'confidence_threshold': 0.4,    # Minimum confidence
            'max_vectors_per_frame': 50     # Maximum vectors per frame
        }
    
    def find_motion_vector_frames(self) -> List[str]:
        """Find all motion vector frames in the motion_vector_art directory."""
        frame_paths = []
        
        # Search motion_vector_art directory
        search_pattern = "/home/mik/VECTOR/motion_vector_art/**/*.png"
        all_frames = glob.glob(search_pattern, recursive=True)
        
        # Filter out analysis files
        for frame_path in all_frames:
            if 'detection_analysis' not in frame_path:
                frame_paths.append(frame_path)
        
        return sorted(frame_paths)
    
    def extract_ffmpeg_vectors(self, frame: np.ndarray) -> List[Dict]:
        """Extract FFmpeg codecview motion vectors (green arrows)."""
        vectors = []
        
        # Convert to HSV for green detection
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Multiple green ranges for better detection
        green_ranges = [
            ([40, 60, 60], [80, 255, 255]),    # Primary green
            ([35, 45, 45], [85, 255, 255]),    # Wider green
            ([45, 80, 80], [75, 255, 255]),    # Saturated green
        ]
        
        for range_idx, (lower, upper) in enumerate(green_ranges):
            green_mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
            
            if cv2.countNonZero(green_mask) > 0:
                contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if 2 <= area <= 50:  # Filter arrow-like shapes
                        # Get contour center
                        M = cv2.moments(contour)
                        if M['m00'] > 0:
                            cx = int(M['m10'] / M['m00'])
                            cy = int(M['m01'] / M['m00'])
                            
                            # Get arrow direction using fitted ellipse
                            if len(contour) >= 5:
                                ellipse = cv2.fitEllipse(contour)
                                (_, _), (width, height), angle = ellipse
                                
                                # Calculate arrow vector
                                magnitude = max(width, height) * self.params['ffmpeg_scale']
                                angle_rad = np.radians(angle)
                                
                                dx = magnitude * np.cos(angle_rad)
                                dy = magnitude * np.sin(angle_rad)
                                
                                # Apply length constraints
                                vector_length = np.sqrt(dx*dx + dy*dy)
                                if vector_length > self.params['max_vector_length']:
                                    scale = self.params['max_vector_length'] / vector_length
                                    dx *= scale
                                    dy *= scale
                                    vector_length = self.params['max_vector_length']
                                
                                if vector_length >= self.params['min_vector_length']:
                                    confidence = 0.9 - range_idx * 0.1  # Higher confidence for primary range
                                    vectors.append({
                                        'center': (cx, cy),
                                        'direction': (dx, dy),
                                        'magnitude': vector_length,
                                        'angle': angle_rad,
                                        'quality': min(area / 50.0, 1.0),
                                        'confidence': confidence,
                                        'method': 'ffmpeg',
                                        'area': area
                                    })
        
        return vectors
    
    def extract_optical_flow_vectors(self, frame: np.ndarray) -> List[Dict]:
        """Extract optical flow vectors."""
        vectors = []
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Create synthetic previous frame for flow calculation
        prev_gray = np.roll(gray, (1, 1), axis=(0, 1))
        
        try:
            # Dense optical flow
            flow = cv2.calcOpticalFlowFarneback(
                prev_gray, gray, None,
                pyr_scale=0.7, levels=2, winsize=8,
                iterations=2, poly_n=3, poly_sigma=1.0, flags=0
            )
            
            # Sample flow vectors at grid points
            h, w = flow.shape[:2]
            step = 25
            
            for y in range(step, h - step, step):
                for x in range(step, w - step, step):
                    fx, fy = flow[y, x]
                    magnitude = np.sqrt(fx*fx + fy*fy)
                    
                    if magnitude > 0.8:  # Significant motion
                        # Scale flow vector
                        dx = fx * self.params['flow_scale']
                        dy = fy * self.params['flow_scale']
                        
                        # Apply length constraints
                        vector_length = np.sqrt(dx*dx + dy*dy)
                        if vector_length > self.params['max_vector_length']:
                            scale = self.params['max_vector_length'] / vector_length
                            dx *= scale
                            dy *= scale
                            vector_length = self.params['max_vector_length']
                        
                        if vector_length >= self.params['min_vector_length']:
                            vectors.append({
                                'center': (x, y),
                                'direction': (dx, dy),
                                'magnitude': vector_length,
                                'angle': np.arctan2(fy, fx),
                                'quality': min(magnitude / 4.0, 1.0),
                                'confidence': 0.7,
                                'method': 'flow',
                                'flow_magnitude': magnitude
                            })
        except Exception as e:
            print(f"  Optical flow failed: {e}")
        
        return vectors
    
    def extract_edge_vectors(self, frame: np.ndarray) -> List[Dict]:
        """Extract edge-based vectors."""
        vectors = []
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Find lines using Hough transform
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=15,
                               minLineLength=6, maxLineGap=3)
        
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                
                # Calculate line properties
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                dx, dy = x2 - x1, y2 - y1
                original_length = np.sqrt(dx*dx + dy*dy)
                
                # Scale and constrain
                dx *= self.params['edge_scale']
                dy *= self.params['edge_scale']
                
                vector_length = np.sqrt(dx*dx + dy*dy)
                if vector_length > self.params['max_vector_length']:
                    scale = self.params['max_vector_length'] / vector_length
                    dx *= scale
                    dy *= scale
                    vector_length = self.params['max_vector_length']
                
                if vector_length >= self.params['min_vector_length']:
                    vectors.append({
                        'center': (cx, cy),
                        'direction': (dx, dy),
                        'magnitude': vector_length,
                        'angle': np.arctan2(dy, dx),
                        'quality': min(original_length / 30.0, 1.0),
                        'confidence': 0.6,
                        'method': 'edge',
                        'original_length': original_length
                    })
        
        return vectors
    
    def extract_motion_vectors_from_frame(self, frame_path: str) -> Dict:
        """Extract all motion vectors from a single frame."""
        frame = cv2.imread(frame_path)
        if frame is None:
            return {'vectors': [], 'error': 'Could not load frame'}
        
        # Resize for processing efficiency
        h, w = frame.shape[:2]
        if max(h, w) > 600:
            scale = 600 / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            frame_resized = cv2.resize(frame, (new_w, new_h))
            scale_back = max(h, w) / 600
        else:
            frame_resized = frame
            scale_back = 1.0
        
        # Extract vectors using all methods
        all_vectors = []
        
        # Method 1: FFmpeg vectors
        ffmpeg_vectors = self.extract_ffmpeg_vectors(frame_resized)
        all_vectors.extend(ffmpeg_vectors)
        
        # Method 2: Optical flow vectors
        flow_vectors = self.extract_optical_flow_vectors(frame_resized)
        all_vectors.extend(flow_vectors)
        
        # Method 3: Edge vectors
        edge_vectors = self.extract_edge_vectors(frame_resized)
        all_vectors.extend(edge_vectors)
        
        # Scale vectors back to original size
        if scale_back != 1.0:
            for vector in all_vectors:
                cx, cy = vector['center']
                dx, dy = vector['direction']
                vector['center'] = (int(cx * scale_back), int(cy * scale_back))
                vector['direction'] = (dx * scale_back * 0.8, dy * scale_back * 0.8)  # Conservative scaling
                vector['magnitude'] *= scale_back * 0.8
        
        # Filter by quality and confidence
        filtered_vectors = []
        for vector in all_vectors:
            if (vector['quality'] >= self.params['quality_threshold'] and 
                vector['confidence'] >= self.params['confidence_threshold']):
                filtered_vectors.append(vector)
        
        # Sort by combined score
        scored_vectors = [(v['quality'] * v['confidence'], v) for v in filtered_vectors]
        scored_vectors.sort(key=lambda x: x[0], reverse=True)
        
        # Remove duplicates
        final_vectors = []
        for score, vector in scored_vectors:
            is_duplicate = False
            for existing in final_vectors:
                dist = np.sqrt((vector['center'][0] - existing['center'][0])**2 + 
                             (vector['center'][1] - existing['center'][1])**2)
                if dist < 15:  # Deduplication distance
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                final_vectors.append(vector)
                if len(final_vectors) >= self.params['max_vectors_per_frame']:
                    break
        
        # Calculate statistics
        method_counts = {}
        for vector in final_vectors:
            method = vector['method']
            method_counts[method] = method_counts.get(method, 0) + 1
        
        lengths = [v['magnitude'] for v in final_vectors]
        qualities = [v['quality'] for v in final_vectors]
        
        return {
            'vectors': final_vectors,
            'frame_path': frame_path,
            'frame_size': (w, h),
            'total_vectors': len(final_vectors),
            'method_distribution': method_counts,
            'length_stats': {
                'min': min(lengths) if lengths else 0,
                'max': max(lengths) if lengths else 0,
                'avg': np.mean(lengths) if lengths else 0
            },
            'quality_stats': {
                'min': min(qualities) if qualities else 0,
                'max': max(qualities) if qualities else 0,
                'avg': np.mean(qualities) if qualities else 0
            }
        }
    
    def process_all_frames(self) -> List[Dict]:
        """Process all frames in motion_vector_art directory."""
        frame_paths = self.find_motion_vector_frames()
        
        if not frame_paths:
            print("❌ No motion vector frames found!")
            return []
        
        print(f"🎬 MOTION VECTOR EXTRACTION")
        print("=" * 50)
        print(f"Found {len(frame_paths)} frames in motion_vector_art directory")
        print(f"Max vector length: {self.params['max_vector_length']}px")
        print(f"GPU acceleration: {'ON' if self.use_gpu else 'OFF'}")
        print("=" * 50)
        
        results = []
        start_time = time.time()
        
        for i, frame_path in enumerate(frame_paths):
            frame_name = Path(frame_path).name
            
            print(f"🎬 Processing [{i+1}/{len(frame_paths)}]: {frame_name}")
            
            result = self.extract_motion_vectors_from_frame(frame_path)
            
            if 'error' in result:
                print(f"  ❌ Error: {result['error']}")
            else:
                vectors = result['vectors']
                method_dist = result['method_distribution']
                length_stats = result['length_stats']
                
                print(f"  📊 Vectors: {len(vectors)} | Methods: {method_dist}")
                print(f"  📏 Lengths: {length_stats['avg']:.1f}px avg, {length_stats['max']:.1f}px max")
                
                # Check length constraints
                constraint_ok = length_stats['max'] <= self.params['max_vector_length']
                status = "✅" if constraint_ok else "⚠️"
                print(f"  {status} Shape preservation: {'GOOD' if constraint_ok else 'CHECK'}")
            
            results.append(result)
        
        elapsed = time.time() - start_time
        
        # Overall statistics
        print("\n" + "=" * 50)
        print("🎬 EXTRACTION COMPLETE")
        print("=" * 50)
        
        valid_results = [r for r in results if 'error' not in r]
        
        if valid_results:
            total_vectors = sum(r['total_vectors'] for r in valid_results)
            all_lengths = []
            all_methods = {}
            
            for result in valid_results:
                for vector in result['vectors']:
                    all_lengths.append(vector['magnitude'])
                    method = vector['method']
                    all_methods[method] = all_methods.get(method, 0) + 1
            
            print(f"Processed frames: {len(valid_results)}")
            print(f"Total vectors extracted: {total_vectors}")
            print(f"Average vectors per frame: {total_vectors/len(valid_results):.1f}")
            print(f"Method distribution: {all_methods}")
            
            if all_lengths:
                print(f"Length statistics:")
                print(f"  Average: {np.mean(all_lengths):.1f}px")
                print(f"  Maximum: {np.max(all_lengths):.1f}px")
                print(f"  Within constraints: {sum(1 for l in all_lengths if l <= self.params['max_vector_length'])} / {len(all_lengths)}")
            
            print(f"Processing time: {elapsed:.1f}s ({elapsed/len(frame_paths):.2f}s per frame)")
        
        return results


class MotionVectorVisualizer:
    """Create visualizations from extracted motion vectors."""
    
    def __init__(self):
        self.output_dir = Path("/home/mik/VECTOR/extracted_motion_vectors")
        self.output_dir.mkdir(exist_ok=True)
        
        self.colors = {
            'ffmpeg': ['#E74C3C', '#C0392B', '#A93226'],     # Red tones
            'flow': ['#3498DB', '#2980B9', '#1F618D'],       # Blue tones  
            'edge': ['#2ECC71', '#27AE60', '#1E8449']        # Green tones
        }
    
    def create_vector_visualization(self, extraction_result: Dict) -> str:
        """Create visualization from extraction result."""
        if 'error' in extraction_result:
            return None
        
        frame_path = extraction_result['frame_path']
        vectors = extraction_result['vectors']
        
        if not vectors:
            return None
        
        # Load original frame
        frame = cv2.imread(frame_path)
        if frame is None:
            return None
        
        h, w = frame.shape[:2]
        frame_name = Path(frame_path).stem
        
        fig, ax = plt.subplots(figsize=(14, 10))
        ax.set_xlim(0, w)
        ax.set_ylim(h, 0)
        ax.set_aspect('equal')
        ax.set_facecolor('#F8F9FA')
        
        # Draw original frame as background (faded)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        ax.imshow(frame_rgb, alpha=0.3, extent=[0, w, h, 0])
        
        # Draw motion vectors by method
        for vector in vectors:
            x, y = vector['center']
            dx, dy = vector['direction']
            method = vector['method']
            quality = vector['quality']
            confidence = vector['confidence']
            
            # Get color for method
            method_colors = self.colors.get(method, ['#7F8C8D'])
            color = method_colors[0]
            
            # Vector styling based on method
            if method == 'ffmpeg':
                arrow_style = '->'
                line_width = 2.5
                mutation_scale = 12
            elif method == 'flow':
                arrow_style = '->'
                line_width = 2.0
                mutation_scale = 10
            else:  # edge
                arrow_style = '-'
                line_width = 1.5
                mutation_scale = 8
            
            alpha = quality * confidence * 0.9
            
            # Draw vector arrow
            arrow = FancyArrowPatch(
                (x, y), (x + dx, y + dy),
                arrowstyle=arrow_style,
                mutation_scale=mutation_scale,
                color=color,
                alpha=alpha,
                linewidth=line_width
            )
            ax.add_patch(arrow)
            
            # Quality indicator for high-quality vectors
            if quality * confidence > 0.8:
                quality_circle = Circle((x, y), 3, color=color, alpha=0.5)
                ax.add_patch(quality_circle)
        
        # Add extraction statistics
        stats = extraction_result
        method_dist = stats['method_distribution']
        length_stats = stats['length_stats']
        
        # Statistics text
        stats_text = [
            f"Vectors: {stats['total_vectors']}",
            f"Methods: {', '.join([f'{k}:{v}' for k, v in method_dist.items()])}",
            f"Lengths: {length_stats['avg']:.1f}px avg, {length_stats['max']:.1f}px max"
        ]
        
        for i, text in enumerate(stats_text):
            ax.text(10, h - 30 - i*20, text, fontsize=11, color='#2C3E50', 
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        # Length constraint status
        constraint_ok = length_stats['max'] <= 18  # Our constraint
        status_text = "✅ SHAPE PRESERVED" if constraint_ok else "⚠️ LENGTH WARNING"
        status_color = 'green' if constraint_ok else 'orange'
        
        ax.text(10, h - 110, status_text, fontsize=12, color=status_color, fontweight='bold',
               bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.9))
        
        # Legend for methods
        legend_elements = []
        for method, colors_list in self.colors.items():
            if method in method_dist:
                legend_elements.append(plt.Line2D([0], [0], color=colors_list[0], lw=2, label=f'{method.title()}: {method_dist[method]}'))
        
        if legend_elements:
            ax.legend(handles=legend_elements, loc='upper right', framealpha=0.9)
        
        ax.set_title(f'Extracted Motion Vectors: {frame_name}', 
                    fontsize=16, fontweight='bold', color='#2C3E50')
        ax.axis('off')
        
        # Save visualization
        output_path = self.output_dir / f"{frame_name}_extracted_vectors.png"
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight',
                   facecolor='#F8F9FA', edgecolor='none')
        plt.close()
        
        return str(output_path)


def main():
    """Main extraction and visualization process."""
    print("🎬 MOTION VECTOR EXTRACTOR")
    print("Extracting motion vectors from motion_vector_art directory")
    
    # Extract motion vectors
    extractor = MotionVectorExtractor()
    extraction_results = extractor.process_all_frames()
    
    # Create visualizations
    print(f"\n🎨 Creating visualizations...")
    visualizer = MotionVectorVisualizer()
    
    created_visualizations = []
    for result in extraction_results:
        if 'error' not in result:
            viz_path = visualizer.create_vector_visualization(result)
            if viz_path:
                created_visualizations.append(viz_path)
    
    print(f"\n✨ Extraction complete!")
    print(f"🎬 Processed {len(extraction_results)} frames")
    print(f"🎨 Created {len(created_visualizations)} visualizations")
    print(f"📁 Output: {visualizer.output_dir}")


if __name__ == "__main__":
    main()