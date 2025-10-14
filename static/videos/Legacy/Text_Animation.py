from manim import *
from numpy import *

class Text_Animation(Scene):

    def construct(self):
        # Turning Background Transparent
        #self.camera.background_opacity = 0

        # White Background if needed
        self.camera.background_color = "#fdf6f1" 
        
        Text = (
            MathTex(r"\mathbb{TEXT}", font_size=120, color=BLACK)
            .set_stroke(color=BLACK, width=0.5, opacity=1)
            
        )

        self.play(Write(Text), run_time=1)
        self.wait(2)
