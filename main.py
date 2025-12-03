"""
LamoEditor Pro - Full-Featured Video Editor
A professional video editing application with timeline, effects, and advanced tools
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QSlider, QStyle, QMessageBox, QTabWidget, QGroupBox,
    QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit, QColorDialog, QProgressBar,
    QListWidget, QSplitter, QScrollArea, QCheckBox, QLineEdit, QToolBar, QMenu
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import Qt, QUrl, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QAction, QKeySequence, QFont, QColor, QPixmap, QImage
from moviepy.editor import (
    VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips,
    vfx, afx, ColorClip
)
from moviepy.video.fx import all as vfx_all
import numpy as np
import threading
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import json


@dataclass
class VideoSegment:
    """Represents a video segment in the timeline"""
    path: str
    start_time: float
    end_time: float
    duration: float
    effects: List[Dict[str, Any]]
    volume: float = 1.0
    speed: float = 1.0
    
    def to_dict(self):
        return {
            'path': self.path,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'effects': self.effects,
            'volume': self.volume,
            'speed': self.speed
        }


@dataclass
class TextOverlay:
    """Represents a text overlay"""
    text: str
    start_time: float
    duration: float
    position: tuple
    font_size: int
    color: str
    font: str = 'Arial'
    
    def to_dict(self):
        return {
            'text': self.text,
            'start_time': self.start_time,
            'duration': self.duration,
            'position': self.position,
            'font_size': self.font_size,
            'color': self.color,
            'font': self.font
        }


class ExportThread(QThread):
    """Thread for exporting video to prevent UI freezing"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, segments, text_overlays, output_path, settings):
        super().__init__()
        self.segments = segments
        self.text_overlays = text_overlays
        self.output_path = output_path
        self.settings = settings
    
    def run(self):
        try:
            clips = []
            
            # Process each segment
            for i, segment in enumerate(self.segments):
                clip = VideoFileClip(segment.path).subclip(segment.start_time, segment.end_time)
                
                # Apply speed
                if segment.speed != 1.0:
                    clip = clip.fx(vfx.speedx, segment.speed)
                
                # Apply effects
                for effect in segment.effects:
                    effect_type = effect.get('type')
                    if effect_type == 'brightness':
                        factor = effect.get('value', 1.0)
                        clip = clip.fx(vfx.colorx, factor)
                    elif effect_type == 'contrast':
                        # Contrast adjustment
                        pass  # MoviePy doesn't have direct contrast, would need custom
                    elif effect_type == 'blur':
                        # Blur effect
                        pass  # Would need custom implementation
                    elif effect_type == 'rotate':
                        angle = effect.get('value', 0)
                        clip = clip.rotate(angle)
                    elif effect_type == 'mirror_x':
                        clip = clip.fx(vfx.mirror_x)
                    elif effect_type == 'mirror_y':
                        clip = clip.fx(vfx.mirror_y)
                    elif effect_type == 'blackwhite':
                        clip = clip.fx(vfx.blackwhite)
                
                # Apply volume
                if clip.audio and segment.volume != 1.0:
                    clip = clip.volumex(segment.volume)
                
                clips.append(clip)
                self.progress.emit(int((i + 1) / len(self.segments) * 50))
            
            # Concatenate clips
            if clips:
                final_clip = concatenate_videoclips(clips, method="compose")
                
                # Add text overlays
                text_clips = []
                for overlay in self.text_overlays:
                    txt_clip = TextClip(
                        overlay.text,
                        fontsize=overlay.font_size,
                        color=overlay.color,
                        font=overlay.font
                    )
                    txt_clip = txt_clip.set_position(overlay.position)
                    txt_clip = txt_clip.set_start(overlay.start_time)
                    txt_clip = txt_clip.set_duration(overlay.duration)
                    text_clips.append(txt_clip)
                
                if text_clips:
                    final_clip = CompositeVideoClip([final_clip] + text_clips)
                
                self.progress.emit(60)
                
                # Export
                codec = self.settings.get('codec', 'libx264')
                bitrate = self.settings.get('bitrate', '5000k')
                fps = self.settings.get('fps', None)
                
                final_clip.write_videofile(
                    self.output_path,
                    codec=codec,
                    audio_codec='aac',
                    bitrate=bitrate,
                    fps=fps,
                    threads=4,
                    verbose=False,
                    logger=None
                )
                
                # Cleanup
                for clip in clips:
                    clip.close()
                final_clip.close()
                
                self.progress.emit(100)
                self.finished.emit(True, self.output_path)
            else:
                self.finished.emit(False, "No clips to export")
                
        except Exception as e:
            self.finished.emit(False, str(e))


class VideoEditorPro(QMainWindow):
    """Professional Video Editor Application"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LamoEditor Pro - Professional Video Editor")
        self.setGeometry(100, 100, 1400, 900)
        
        # State
        self.current_video_path = None
        self.video_segments: List[VideoSegment] = []
        self.text_overlays: List[TextOverlay] = []
        self.undo_stack = []
        self.redo_stack = []
        self.clip_duration = 0.0
        self.in_time = 0.0
        self.out_time = 0.0
        self.updating_slider = False
        self.current_segment_index = -1
        
        # Setup UI
        self.setup_ui()
        self.setup_menu_bar()
        self.setup_toolbar()
        self.setup_shortcuts()
        
        # Timer for updating time display
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time_display)
        self.timer.start(100)
    
    def setup_ui(self):
        """Setup the main user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Video preview and controls
        left_panel = self.create_preview_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Effects and tools
        right_panel = self.create_tools_panel()
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)
        
        # Bottom panel - Timeline
        timeline_panel = self.create_timeline_panel()
        main_layout.addWidget(timeline_panel)
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def create_preview_panel(self):
        """Create video preview panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Video widget
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.video_widget = QVideoWidget(self)
        self.player.setVideoOutput(self.video_widget)
        self.video_widget.setMinimumHeight(400)
        layout.addWidget(self.video_widget, 3)
        
        # Playback controls
        controls_layout = QHBoxLayout()
        
        self.open_btn = QPushButton("Open Video")
        self.open_btn.clicked.connect(self.open_video)
        controls_layout.addWidget(self.open_btn)
        
        self.play_btn = QPushButton(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay), "")
        self.play_btn.clicked.connect(self.toggle_play)
        controls_layout.addWidget(self.play_btn)
        
        self.stop_btn = QPushButton(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop), "")
        self.stop_btn.clicked.connect(self.stop_playback)
        controls_layout.addWidget(self.stop_btn)
        
        self.set_in_btn = QPushButton("Set In [I]")
        self.set_in_btn.clicked.connect(self.set_in_point)
        controls_layout.addWidget(self.set_in_btn)
        
        self.set_out_btn = QPushButton("Set Out [O]")
        self.set_out_btn.clicked.connect(self.set_out_point)
        controls_layout.addWidget(self.set_out_btn)
        
        self.add_segment_btn = QPushButton("Add to Timeline")
        self.add_segment_btn.clicked.connect(self.add_segment_to_timeline)
        controls_layout.addWidget(self.add_segment_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Timeline slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 1000)
        self.slider.sliderMoved.connect(self.on_slider_moved)
        self.slider.sliderPressed.connect(lambda: setattr(self, 'updating_slider', True))
        self.slider.sliderReleased.connect(lambda: setattr(self, 'updating_slider', False))
        layout.addWidget(self.slider)
        
        # Time display
        time_layout = QHBoxLayout()
        self.current_time_label = QLabel("00:00:00")
        self.duration_label = QLabel("00:00:00")
        self.in_label = QLabel("In: 00:00:00")
        self.out_label = QLabel("Out: 00:00:00")
        
        time_layout.addWidget(QLabel("Current:"))
        time_layout.addWidget(self.current_time_label)
        time_layout.addWidget(QLabel("Duration:"))
        time_layout.addWidget(self.duration_label)
        time_layout.addStretch()
        time_layout.addWidget(self.in_label)
        time_layout.addWidget(self.out_label)
        
        layout.addLayout(time_layout)
        
        # Connect player signals
        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)
        
        return panel
    
    def create_tools_panel(self):
        """Create tools and effects panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Tabs for different tool categories
        tabs = QTabWidget()
        
        # Effects tab
        effects_tab = self.create_effects_tab()
        tabs.addTab(effects_tab, "Effects")
        
        # Text tab
        text_tab = self.create_text_tab()
        tabs.addTab(text_tab, "Text")
        
        # Audio tab
        audio_tab = self.create_audio_tab()
        tabs.addTab(audio_tab, "Audio")
        
        # Export tab
        export_tab = self.create_export_tab()
        tabs.addTab(export_tab, "Export")
        
        layout.addWidget(tabs)
        
        return panel
    
    def create_effects_tab(self):
        """Create effects controls"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Color adjustments
        color_group = QGroupBox("Color Adjustments")
        color_layout = QVBoxLayout()
        
        # Brightness
        brightness_layout = QHBoxLayout()
        brightness_layout.addWidget(QLabel("Brightness:"))
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setRange(0, 200)
        self.brightness_slider.setValue(100)
        self.brightness_value = QLabel("1.0")
        brightness_layout.addWidget(self.brightness_slider)
        brightness_layout.addWidget(self.brightness_value)
        self.brightness_slider.valueChanged.connect(
            lambda v: self.brightness_value.setText(f"{v/100:.1f}")
        )
        color_layout.addLayout(brightness_layout)
        
        # Contrast
        contrast_layout = QHBoxLayout()
        contrast_layout.addWidget(QLabel("Contrast:"))
        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setRange(0, 200)
        self.contrast_slider.setValue(100)
        self.contrast_value = QLabel("1.0")
        contrast_layout.addWidget(self.contrast_slider)
        contrast_layout.addWidget(self.contrast_value)
        self.contrast_slider.valueChanged.connect(
            lambda v: self.contrast_value.setText(f"{v/100:.1f}")
        )
        color_layout.addLayout(contrast_layout)
        
        color_group.setLayout(color_layout)
        scroll_layout.addWidget(color_group)
        
        # Transform
        transform_group = QGroupBox("Transform")
        transform_layout = QVBoxLayout()
        
        # Rotation
        rotation_layout = QHBoxLayout()
        rotation_layout.addWidget(QLabel("Rotate:"))
        self.rotation_spin = QSpinBox()
        self.rotation_spin.setRange(-360, 360)
        self.rotation_spin.setSuffix("°")
        rotation_layout.addWidget(self.rotation_spin)
        transform_layout.addLayout(rotation_layout)
        
        # Speed
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Speed:"))
        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(0.1, 10.0)
        self.speed_spin.setValue(1.0)
        self.speed_spin.setSingleStep(0.1)
        self.speed_spin.setSuffix("x")
        speed_layout.addWidget(self.speed_spin)
        transform_layout.addLayout(speed_layout)
        
        transform_group.setLayout(transform_layout)
        scroll_layout.addWidget(transform_group)
        
        # Filters
        filters_group = QGroupBox("Filters")
        filters_layout = QVBoxLayout()
        
        self.blackwhite_check = QCheckBox("Black & White")
        filters_layout.addWidget(self.blackwhite_check)
        
        self.mirror_x_check = QCheckBox("Mirror Horizontal")
        filters_layout.addWidget(self.mirror_x_check)
        
        self.mirror_y_check = QCheckBox("Mirror Vertical")
        filters_layout.addWidget(self.mirror_y_check)
        
        filters_group.setLayout(filters_layout)
        scroll_layout.addWidget(filters_group)
        
        # Apply button
        apply_effects_btn = QPushButton("Apply Effects to Selected Segment")
        apply_effects_btn.clicked.connect(self.apply_effects)
        scroll_layout.addWidget(apply_effects_btn)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        
        layout.addWidget(scroll)
        
        return tab
    
    def create_text_tab(self):
        """Create text overlay controls"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Text input
        layout.addWidget(QLabel("Text:"))
        self.text_input = QTextEdit()
        self.text_input.setMaximumHeight(100)
        layout.addWidget(self.text_input)
        
        # Font settings
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("Font:"))
        self.font_combo = QComboBox()
        self.font_combo.addItems(['Arial', 'Times-New-Roman', 'Courier', 'Helvetica', 'Comic-Sans-MS'])
        font_layout.addWidget(self.font_combo)
        layout.addLayout(font_layout)
        
        # Font size
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Size:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(10, 200)
        self.font_size_spin.setValue(50)
        size_layout.addWidget(self.font_size_spin)
        layout.addLayout(size_layout)
        
        # Color
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Color:"))
        self.text_color_btn = QPushButton("Choose Color")
        self.text_color = 'white'
        self.text_color_btn.clicked.connect(self.choose_text_color)
        color_layout.addWidget(self.text_color_btn)
        layout.addLayout(color_layout)
        
        # Position
        position_layout = QHBoxLayout()
        position_layout.addWidget(QLabel("Position:"))
        self.position_combo = QComboBox()
        self.position_combo.addItems(['center', 'top', 'bottom', 'left', 'right'])
        position_layout.addWidget(self.position_combo)
        layout.addLayout(position_layout)
        
        # Duration
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Duration (s):"))
        self.text_duration_spin = QDoubleSpinBox()
        self.text_duration_spin.setRange(0.1, 3600)
        self.text_duration_spin.setValue(5.0)
        duration_layout.addWidget(self.text_duration_spin)
        layout.addLayout(duration_layout)
        
        # Add text button
        add_text_btn = QPushButton("Add Text Overlay")
        add_text_btn.clicked.connect(self.add_text_overlay)
        layout.addWidget(add_text_btn)
        
        # Text overlays list
        layout.addWidget(QLabel("Text Overlays:"))
        self.text_list = QListWidget()
        layout.addWidget(self.text_list)
        
        # Remove text button
        remove_text_btn = QPushButton("Remove Selected")
        remove_text_btn.clicked.connect(self.remove_text_overlay)
        layout.addWidget(remove_text_btn)
        
        layout.addStretch()
        
        return tab
    
    def create_audio_tab(self):
        """Create audio controls"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Volume control
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 200)
        self.volume_slider.setValue(100)
        self.volume_value = QLabel("100%")
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addWidget(self.volume_value)
        self.volume_slider.valueChanged.connect(
            lambda v: self.volume_value.setText(f"{v}%")
        )
        layout.addLayout(volume_layout)
        
        # Apply volume button
        apply_volume_btn = QPushButton("Apply Volume to Selected Segment")
        apply_volume_btn.clicked.connect(self.apply_volume)
        layout.addWidget(apply_volume_btn)
        
        layout.addStretch()
        
        return tab
    
    def create_export_tab(self):
        """Create export controls"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(['MP4 (H.264)', 'MP4 (H.265)', 'AVI', 'MOV', 'WebM'])
        format_layout.addWidget(self.format_combo)
        layout.addLayout(format_layout)
        
        # Quality/Bitrate
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Bitrate:"))
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(['2000k (Low)', '5000k (Medium)', '8000k (High)', '15000k (Very High)'])
        self.bitrate_combo.setCurrentIndex(1)
        quality_layout.addWidget(self.bitrate_combo)
        layout.addLayout(quality_layout)
        
        # FPS
        fps_layout = QHBoxLayout()
        fps_layout.addWidget(QLabel("FPS:"))
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(['Original', '24', '30', '60'])
        fps_layout.addWidget(self.fps_combo)
        layout.addLayout(fps_layout)
        
        # Progress bar
        self.export_progress = QProgressBar()
        self.export_progress.setVisible(False)
        layout.addWidget(self.export_progress)
        
        # Export button
        self.export_btn = QPushButton("Export Video")
        self.export_btn.clicked.connect(self.export_video)
        layout.addWidget(self.export_btn)
        
        layout.addStretch()
        
        return tab
    
    def create_timeline_panel(self):
        """Create timeline panel"""
        panel = QGroupBox("Timeline")
        layout = QVBoxLayout(panel)
        
        # Timeline list
        self.timeline_list = QListWidget()
        self.timeline_list.itemClicked.connect(self.on_timeline_item_clicked)
        layout.addWidget(self.timeline_list)
        
        # Timeline controls
        controls_layout = QHBoxLayout()
        
        move_up_btn = QPushButton("Move Up")
        move_up_btn.clicked.connect(self.move_segment_up)
        controls_layout.addWidget(move_up_btn)
        
        move_down_btn = QPushButton("Move Down")
        move_down_btn.clicked.connect(self.move_segment_down)
        controls_layout.addWidget(move_down_btn)
        
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self.remove_segment)
        controls_layout.addWidget(remove_btn)
        
        clear_btn = QPushButton("Clear Timeline")
        clear_btn.clicked.connect(self.clear_timeline)
        controls_layout.addWidget(clear_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        panel.setMaximumHeight(200)
        
        return panel
    
    def setup_menu_bar(self):
        """Setup menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        open_action = QAction("Open Video", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_video)
        file_menu.addAction(open_action)
        
        save_project_action = QAction("Save Project", self)
        save_project_action.setShortcut(QKeySequence.StandardKey.Save)
        save_project_action.triggered.connect(self.save_project)
        file_menu.addAction(save_project_action)
        
        load_project_action = QAction("Load Project", self)
        load_project_action.triggered.connect(self.load_project)
        file_menu.addAction(load_project_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        undo_action = QAction("Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_toolbar(self):
        """Setup toolbar"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        toolbar.addAction(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton), 
                         "Open", self.open_video)
        toolbar.addSeparator()
        toolbar.addAction(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay), 
                         "Play", self.toggle_play)
        toolbar.addAction(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop), 
                         "Stop", self.stop_playback)
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Spacebar for play/pause
        play_shortcut = QKeySequence(Qt.Key.Key_Space)
        play_action = QAction(self)
        play_action.setShortcut(play_shortcut)
        play_action.triggered.connect(self.toggle_play)
        self.addAction(play_action)
        
        # I for in point
        in_shortcut = QKeySequence(Qt.Key.Key_I)
        in_action = QAction(self)
        in_action.setShortcut(in_shortcut)
        in_action.triggered.connect(self.set_in_point)
        self.addAction(in_action)
        
        # O for out point
        out_shortcut = QKeySequence(Qt.Key.Key_O)
        out_action = QAction(self)
        out_action.setShortcut(out_shortcut)
        out_action.triggered.connect(self.set_out_point)
        self.addAction(out_action)
    
    # Video playback methods
    def open_video(self):
        """Open a video file"""
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Video", "", 
            "Videos (*.mp4 *.mov *.mkv *.avi *.webm *.flv)"
        )
        if not path:
            return
        
        self.current_video_path = path
        url = QUrl.fromLocalFile(path)
        self.player.setSource(url)
        
        # Load duration
        try:
            clip = VideoFileClip(path)
            self.clip_duration = float(clip.duration)
            clip.close()
            self.out_time = self.clip_duration
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not read video: {e}")
            self.clip_duration = 0.0
        
        self.in_time = 0.0
        self.update_time_labels()
        self.statusBar().showMessage(f"Loaded: {Path(path).name}")
    
    def toggle_play(self):
        """Toggle play/pause"""
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        else:
            self.player.play()
            self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
    
    def stop_playback(self):
        """Stop playback"""
        self.player.stop()
        self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
    
    def set_in_point(self):
        """Set in point"""
        pos_ms = self.player.position()
        self.in_time = pos_ms / 1000.0
        if self.in_time < 0:
            self.in_time = 0.0
        if self.out_time and self.in_time > self.out_time:
            self.out_time = self.in_time
        self.update_time_labels()
    
    def set_out_point(self):
        """Set out point"""
        pos_ms = self.player.position()
        self.out_time = pos_ms / 1000.0
        if self.out_time > self.clip_duration:
            self.out_time = self.clip_duration
        if self.out_time < self.in_time:
            self.in_time = self.out_time
        self.update_time_labels()
    
    def on_position_changed(self, pos):
        """Handle position change"""
        if self.updating_slider or self.clip_duration <= 0:
            return
        frac = pos / (self.clip_duration * 1000.0)
        self.slider.setValue(int(frac * 1000))
    
    def on_duration_changed(self, dur):
        """Handle duration change"""
        if dur > 0 and self.clip_duration == 0:
            self.clip_duration = dur / 1000.0
            self.out_time = self.clip_duration
            self.update_time_labels()
    
    def on_slider_moved(self, val):
        """Handle slider movement"""
        if self.clip_duration <= 0:
            return
        t = (val / 1000.0) * self.clip_duration
        self.player.setPosition(int(t * 1000))
    
    def update_time_display(self):
        """Update time display"""
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            pos = self.player.position() / 1000.0
            self.current_time_label.setText(self.format_time(pos))
    
    def update_time_labels(self):
        """Update time labels"""
        self.duration_label.setText(self.format_time(self.clip_duration))
        self.in_label.setText(f"In: {self.format_time(self.in_time)}")
        self.out_label.setText(f"Out: {self.format_time(self.out_time)}")
    
    @staticmethod
    def format_time(seconds):
        """Format time as HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    # Timeline methods
    def add_segment_to_timeline(self):
        """Add current segment to timeline"""
        if not self.current_video_path:
            QMessageBox.information(self, "No Video", "Please open a video first.")
            return
        
        if self.in_time >= self.out_time:
            QMessageBox.warning(self, "Invalid Range", "Out point must be after in point.")
            return
        
        segment = VideoSegment(
            path=self.current_video_path,
            start_time=self.in_time,
            end_time=self.out_time,
            duration=self.out_time - self.in_time,
            effects=[],
            volume=1.0,
            speed=1.0
        )
        
        self.save_state()
        self.video_segments.append(segment)
        self.update_timeline_display()
        self.statusBar().showMessage(f"Added segment: {segment.duration:.2f}s")
    
    def update_timeline_display(self):
        """Update timeline display"""
        self.timeline_list.clear()
        total_duration = 0
        for i, segment in enumerate(self.video_segments):
            name = Path(segment.path).name
            item_text = f"{i+1}. {name} ({segment.start_time:.2f}s - {segment.end_time:.2f}s) [{segment.duration:.2f}s]"
            if segment.speed != 1.0:
                item_text += f" Speed: {segment.speed}x"
            if segment.effects:
                item_text += f" Effects: {len(segment.effects)}"
            self.timeline_list.addItem(item_text)
            total_duration += segment.duration / segment.speed
        
        self.statusBar().showMessage(f"Timeline: {len(self.video_segments)} segments, {total_duration:.2f}s total")
    
    def on_timeline_item_clicked(self, item):
        """Handle timeline item click"""
        self.current_segment_index = self.timeline_list.row(item)
    
    def move_segment_up(self):
        """Move selected segment up"""
        if self.current_segment_index > 0:
            self.save_state()
            idx = self.current_segment_index
            self.video_segments[idx], self.video_segments[idx-1] = \
                self.video_segments[idx-1], self.video_segments[idx]
            self.current_segment_index -= 1
            self.update_timeline_display()
            self.timeline_list.setCurrentRow(self.current_segment_index)
    
    def move_segment_down(self):
        """Move selected segment down"""
        if 0 <= self.current_segment_index < len(self.video_segments) - 1:
            self.save_state()
            idx = self.current_segment_index
            self.video_segments[idx], self.video_segments[idx+1] = \
                self.video_segments[idx+1], self.video_segments[idx]
            self.current_segment_index += 1
            self.update_timeline_display()
            self.timeline_list.setCurrentRow(self.current_segment_index)
    
    def remove_segment(self):
        """Remove selected segment"""
        if 0 <= self.current_segment_index < len(self.video_segments):
            self.save_state()
            del self.video_segments[self.current_segment_index]
            self.current_segment_index = -1
            self.update_timeline_display()
    
    def clear_timeline(self):
        """Clear all segments"""
        reply = QMessageBox.question(
            self, "Clear Timeline", 
            "Are you sure you want to clear the timeline?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.save_state()
            self.video_segments.clear()
            self.update_timeline_display()
    
    # Effects methods
    def apply_effects(self):
        """Apply effects to selected segment"""
        if self.current_segment_index < 0 or self.current_segment_index >= len(self.video_segments):
            QMessageBox.information(self, "No Selection", "Please select a segment from the timeline.")
            return
        
        self.save_state()
        segment = self.video_segments[self.current_segment_index]
        segment.effects.clear()
        
        # Brightness
        brightness = self.brightness_slider.value() / 100.0
        if brightness != 1.0:
            segment.effects.append({'type': 'brightness', 'value': brightness})
        
        # Contrast
        contrast = self.contrast_slider.value() / 100.0
        if contrast != 1.0:
            segment.effects.append({'type': 'contrast', 'value': contrast})
        
        # Rotation
        rotation = self.rotation_spin.value()
        if rotation != 0:
            segment.effects.append({'type': 'rotate', 'value': rotation})
        
        # Speed
        speed = self.speed_spin.value()
        segment.speed = speed
        
        # Filters
        if self.blackwhite_check.isChecked():
            segment.effects.append({'type': 'blackwhite'})
        
        if self.mirror_x_check.isChecked():
            segment.effects.append({'type': 'mirror_x'})
        
        if self.mirror_y_check.isChecked():
            segment.effects.append({'type': 'mirror_y'})
        
        self.update_timeline_display()
        self.statusBar().showMessage(f"Applied {len(segment.effects)} effects to segment {self.current_segment_index + 1}")
    
    def apply_volume(self):
        """Apply volume to selected segment"""
        if self.current_segment_index < 0 or self.current_segment_index >= len(self.video_segments):
            QMessageBox.information(self, "No Selection", "Please select a segment from the timeline.")
            return
        
        self.save_state()
        volume = self.volume_slider.value() / 100.0
        self.video_segments[self.current_segment_index].volume = volume
        self.statusBar().showMessage(f"Set volume to {volume*100:.0f}% for segment {self.current_segment_index + 1}")
    
    # Text overlay methods
    def choose_text_color(self):
        """Choose text color"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.text_color = color.name()
            self.text_color_btn.setStyleSheet(f"background-color: {self.text_color}")
    
    def add_text_overlay(self):
        """Add text overlay"""
        text = self.text_input.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "No Text", "Please enter some text.")
            return
        
        position_map = {
            'center': 'center',
            'top': ('center', 'top'),
            'bottom': ('center', 'bottom'),
            'left': ('left', 'center'),
            'right': ('right', 'center')
        }
        
        overlay = TextOverlay(
            text=text,
            start_time=self.in_time,
            duration=self.text_duration_spin.value(),
            position=position_map[self.position_combo.currentText()],
            font_size=self.font_size_spin.value(),
            color=self.text_color,
            font=self.font_combo.currentText()
        )
        
        self.save_state()
        self.text_overlays.append(overlay)
        self.text_list.addItem(f"{overlay.text[:30]}... at {overlay.start_time:.2f}s ({overlay.duration:.2f}s)")
        self.statusBar().showMessage(f"Added text overlay")
    
    def remove_text_overlay(self):
        """Remove selected text overlay"""
        current_row = self.text_list.currentRow()
        if current_row >= 0:
            self.save_state()
            del self.text_overlays[current_row]
            self.text_list.takeItem(current_row)
    
    # Export methods
    def export_video(self):
        """Export final video"""
        if not self.video_segments:
            QMessageBox.information(self, "Empty Timeline", "Please add segments to the timeline first.")
            return
        
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Save Video", "output.mp4", 
            "MP4 (*.mp4);;AVI (*.avi);;MOV (*.mov);;WebM (*.webm)"
        )
        if not output_path:
            return
        
        # Get export settings
        format_text = self.format_combo.currentText()
        codec_map = {
            'MP4 (H.264)': 'libx264',
            'MP4 (H.265)': 'libx265',
            'AVI': 'png',
            'MOV': 'libx264',
            'WebM': 'libvpx'
        }
        codec = codec_map.get(format_text, 'libx264')
        
        bitrate = self.bitrate_combo.currentText().split()[0]
        
        fps_text = self.fps_combo.currentText()
        fps = None if fps_text == 'Original' else int(fps_text)
        
        settings = {
            'codec': codec,
            'bitrate': bitrate,
            'fps': fps
        }
        
        # Start export thread
        self.export_btn.setEnabled(False)
        self.export_progress.setVisible(True)
        self.export_progress.setValue(0)
        
        self.export_thread = ExportThread(
            self.video_segments,
            self.text_overlays,
            output_path,
            settings
        )
        self.export_thread.progress.connect(self.export_progress.setValue)
        self.export_thread.finished.connect(self.on_export_finished)
        self.export_thread.start()
        
        self.statusBar().showMessage("Exporting video...")
    
    def on_export_finished(self, success, message):
        """Handle export completion"""
        self.export_btn.setEnabled(True)
        self.export_progress.setVisible(False)
        
        if success:
            QMessageBox.information(self, "Export Complete", f"Video exported successfully:\n{message}")
            self.statusBar().showMessage("Export complete")
        else:
            QMessageBox.critical(self, "Export Failed", f"Export failed:\n{message}")
            self.statusBar().showMessage("Export failed")
    
    # Project management
    def save_project(self):
        """Save project to file"""
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Project", "project.json", "JSON (*.json)"
        )
        if not path:
            return
        
        project_data = {
            'segments': [seg.to_dict() for seg in self.video_segments],
            'text_overlays': [overlay.to_dict() for overlay in self.text_overlays]
        }
        
        try:
            with open(path, 'w') as f:
                json.dump(project_data, f, indent=2)
            self.statusBar().showMessage(f"Project saved: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Could not save project:\n{e}")
    
    def load_project(self):
        """Load project from file"""
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Project", "", "JSON (*.json)"
        )
        if not path:
            return
        
        try:
            with open(path, 'r') as f:
                project_data = json.load(f)
            
            self.video_segments.clear()
            self.text_overlays.clear()
            
            for seg_data in project_data.get('segments', []):
                segment = VideoSegment(**seg_data)
                self.video_segments.append(segment)
            
            for overlay_data in project_data.get('text_overlays', []):
                overlay = TextOverlay(**overlay_data)
                self.text_overlays.append(overlay)
            
            self.update_timeline_display()
            self.text_list.clear()
            for overlay in self.text_overlays:
                self.text_list.addItem(f"{overlay.text[:30]}... at {overlay.start_time:.2f}s")
            
            self.statusBar().showMessage(f"Project loaded: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Could not load project:\n{e}")
    
    # Undo/Redo
    def save_state(self):
        """Save current state for undo"""
        state = {
            'segments': [seg.to_dict() for seg in self.video_segments],
            'text_overlays': [overlay.to_dict() for overlay in self.text_overlays]
        }
        self.undo_stack.append(json.dumps(state))
        self.redo_stack.clear()
        
        # Limit undo stack size
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)
    
    def undo(self):
        """Undo last action"""
        if not self.undo_stack:
            return
        
        # Save current state to redo stack
        current_state = {
            'segments': [seg.to_dict() for seg in self.video_segments],
            'text_overlays': [overlay.to_dict() for overlay in self.text_overlays]
        }
        self.redo_stack.append(json.dumps(current_state))
        
        # Restore previous state
        state_json = self.undo_stack.pop()
        self.restore_state(state_json)
        self.statusBar().showMessage("Undo")
    
    def redo(self):
        """Redo last undone action"""
        if not self.redo_stack:
            return
        
        # Save current state to undo stack
        current_state = {
            'segments': [seg.to_dict() for seg in self.video_segments],
            'text_overlays': [overlay.to_dict() for overlay in self.text_overlays]
        }
        self.undo_stack.append(json.dumps(current_state))
        
        # Restore redo state
        state_json = self.redo_stack.pop()
        self.restore_state(state_json)
        self.statusBar().showMessage("Redo")
    
    def restore_state(self, state_json):
        """Restore state from JSON"""
        state = json.loads(state_json)
        
        self.video_segments.clear()
        for seg_data in state.get('segments', []):
            segment = VideoSegment(**seg_data)
            self.video_segments.append(segment)
        
        self.text_overlays.clear()
        for overlay_data in state.get('text_overlays', []):
            overlay = TextOverlay(**overlay_data)
            self.text_overlays.append(overlay)
        
        self.update_timeline_display()
        self.text_list.clear()
        for overlay in self.text_overlays:
            self.text_list.addItem(f"{overlay.text[:30]}... at {overlay.start_time:.2f}s")
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self, "About LamoEditor Pro",
            "<h2>LamoEditor Pro</h2>"
            "<p>Professional Video Editor</p>"
            "<p>Features:</p>"
            "<ul>"
            "<li>Multi-segment timeline editing</li>"
            "<li>Video effects and filters</li>"
            "<li>Text overlays</li>"
            "<li>Audio control</li>"
            "<li>Multiple export formats</li>"
            "<li>Undo/Redo support</li>"
            "<li>Project save/load</li>"
            "</ul>"
            "<p>Built with PyQt6 and MoviePy</p>"
        )


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    
    window = VideoEditorPro()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
