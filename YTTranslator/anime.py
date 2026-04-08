#!/usr/bin/env python3
"""
Anime Video Transformer
Converts videos to anime/cartoon style using AnimeGANv2
"""

import os
import cv2
import numpy as np
import torch
from pathlib import Path
from tqdm import tqdm
import urllib.request
import warnings
warnings.filterwarnings('ignore')

class AnimeTransformer:
    def __init__(self, model_path='models'):
        """Initialize the anime transformer"""
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_path = Path(model_path)
        self.model_path.mkdir(exist_ok=True)
        self.model = None
        print(f"🎨 Using device: {self.device}")
        
    def download_model(self):
        """Download AnimeGANv2 model if not exists"""
        model_file = self.model_path / 'AnimeGANv2_Hayao.onnx'
        
        if model_file.exists():
            print("✓ Model already downloaded")
            return str(model_file)
        
        print("📥 Downloading AnimeGANv2 model (Hayao style)...")
        url = "https://github.com/TachibanaYoshino/AnimeGANv2/releases/download/1.0/AnimeGANv2_Hayao.onnx"
        
        try:
            urllib.request.urlretrieve(url, str(model_file))
            print("✓ Model downloaded successfully")
            return str(model_file)
        except Exception as e:
            print(f"❌ Error downloading model: {e}")
            print("Falling back to edge-based cartoon filter...")
            return None
    
    def load_model(self):
        """Load the AnimeGANv2 ONNX model"""
        model_file = self.download_model()
        
        if model_file and os.path.exists(model_file):
            try:
                import onnxruntime as ort
                self.model = ort.InferenceSession(model_file, providers=['CPUExecutionProvider'])
                print("✓ AnimeGANv2 model loaded successfully")
                return True
            except ImportError:
                print("⚠️  onnxruntime not installed. Install with: pip install onnxruntime")
                return False
            except Exception as e:
                print(f"⚠️  Error loading model: {e}")
                return False
        return False
    
    def preprocess_frame(self, frame):
        """Preprocess frame for model input"""
        # Resize maintaining aspect ratio if needed
        h, w = frame.shape[:2]
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Normalize to [-1, 1]
        frame_normalized = (frame_rgb.astype(np.float32) - 127.5) / 127.5
        
        # Add batch dimension and transpose to NCHW format
        frame_input = np.transpose(frame_normalized, (2, 0, 1))
        frame_input = np.expand_dims(frame_input, axis=0).astype(np.float32)
        
        return frame_input
    
    def postprocess_frame(self, output):
        """Postprocess model output to image"""
        # Remove batch dimension and transpose to HWC
        output = np.squeeze(output, axis=0)
        output = np.transpose(output, (1, 2, 0))
        
        # Denormalize from [-1, 1] to [0, 255]
        output = ((output + 1) * 127.5).clip(0, 255).astype(np.uint8)
        
        # Convert RGB to BGR for OpenCV
        output_bgr = cv2.cvtColor(output, cv2.COLOR_RGB2BGR)
        
        return output_bgr
    
    def cartoon_filter(self, frame):
        """Fallback cartoon filter using edge detection and bilateral filter"""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 5)
        
        # Detect edges
        edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                      cv2.THRESH_BINARY, 9, 9)
        
        # Bilateral filter for smoothing while preserving edges
        color = cv2.bilateralFilter(frame, 9, 300, 300)
        
        # Combine edges with color
        cartoon = cv2.bitwise_and(color, color, mask=edges)
        
        # Enhance colors
        hsv = cv2.cvtColor(cartoon, cv2.COLOR_BGR2HSV)
        hsv[:, :, 1] = cv2.add(hsv[:, :, 1], 30)  # Increase saturation
        cartoon_enhanced = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        # Apply slight smoothing
        cartoon_final = cv2.bilateralFilter(cartoon_enhanced, 5, 50, 50)
        
        return cartoon_final
    
    def transform_frame(self, frame):
        """Transform a single frame to anime style"""
        if self.model is not None:
            try:
                # Use AnimeGANv2
                input_data = self.preprocess_frame(frame)
                output = self.model.run(None, {self.model.get_inputs()[0].name: input_data})
                return self.postprocess_frame(output[0])
            except Exception as e:
                print(f"⚠️  Model inference error: {e}, using cartoon filter")
                return self.cartoon_filter(frame)
        else:
            # Use cartoon filter as fallback
            return self.cartoon_filter(frame)
    
    def get_video_files(self, folder_path):
        """Get all video files from folder"""
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.m4v', '.webm'}
        folder = Path(folder_path)
        
        if not folder.exists():
            print(f"❌ Folder '{folder_path}' not found!")
            return []
        
        video_files = [f for f in folder.iterdir() 
                      if f.is_file() and f.suffix.lower() in video_extensions]
        
        return video_files
    
    def process_video(self, input_path, output_path, target_resolution=(1920, 1080)):
        """Process a single video file"""
        print(f"\n🎬 Processing: {input_path.name}")
        
        # Open video
        cap = cv2.VideoCapture(str(input_path))
        
        if not cap.isOpened():
            print(f"❌ Cannot open video: {input_path}")
            return False
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"📊 Original: {original_width}x{original_height} @ {fps} FPS")
        print(f"📊 Output: {target_resolution[0]}x{target_resolution[1]} @ {fps} FPS")
        print(f"📊 Total frames: {total_frames}")
        
        # Setup video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_path), fourcc, fps, target_resolution)
        
        if not out.isOpened():
            print(f"❌ Cannot create output video: {output_path}")
            cap.release()
            return False
        
        # Process frames
        frame_count = 0
        with tqdm(total=total_frames, desc="Converting", unit="frame") as pbar:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Resize to target resolution
                if (original_width, original_height) != target_resolution:
                    frame = cv2.resize(frame, target_resolution, interpolation=cv2.INTER_LANCZOS4)
                
                # Transform to anime style
                anime_frame = self.transform_frame(frame)
                
                # Ensure output is correct size
                if anime_frame.shape[:2][::-1] != target_resolution:
                    anime_frame = cv2.resize(anime_frame, target_resolution, interpolation=cv2.INTER_LANCZOS4)
                
                # Write frame
                out.write(anime_frame)
                
                frame_count += 1
                pbar.update(1)
        
        # Cleanup
        cap.release()
        out.release()
        
        print(f"✓ Successfully processed {frame_count} frames")
        print(f"✓ Saved to: {output_path}")
        
        return True
    
    def process_folder(self, input_folder='ForAnime', output_folder='AnimeOutput'):
        """Process all videos in folder"""
        print("=" * 60)
        print("🎨 ANIME VIDEO TRANSFORMER")
        print("=" * 60)
        
        # Load model
        self.load_model()
        
        # Get video files
        video_files = self.get_video_files(input_folder)
        
        if not video_files:
            print(f"\n❌ No video files found in '{input_folder}' folder")
            print(f"📁 Please place your videos in the '{input_folder}' folder")
            return
        
        print(f"\n📁 Found {len(video_files)} video(s):")
        for i, video in enumerate(video_files, 1):
            print(f"   {i}. {video.name}")
        
        # Create output folder
        output_path = Path(output_folder)
        output_path.mkdir(exist_ok=True)
        
        # Process each video
        success_count = 0
        for video in video_files:
            output_file = output_path / f"anime_{video.stem}.mp4"
            
            if self.process_video(video, output_file):
                success_count += 1
        
        print("\n" + "=" * 60)
        print(f"✨ COMPLETED: {success_count}/{len(video_files)} videos processed")
        print(f"📂 Output folder: {output_folder}")
        print("=" * 60)


def main():
    """Main function"""
    # Configuration
    INPUT_FOLDER = 'ForAnime'
    OUTPUT_FOLDER = 'AnimeOutput'
    
    # Create input folder if it doesn't exist
    Path(INPUT_FOLDER).mkdir(exist_ok=True)
    
    # Initialize and run transformer
    transformer = AnimeTransformer()
    transformer.process_folder(INPUT_FOLDER, OUTPUT_FOLDER)
    
    print("\n💡 TIP: For best results, install onnxruntime:")
    print("   pip install onnxruntime")


if __name__ == "__main__":
    main()