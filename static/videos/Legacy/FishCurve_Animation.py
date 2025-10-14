from manim import *
from numpy import *

# Fish curve class
class Fishcurve(VMobject):
    def __init__(self, w=6, h=3, k=10, range = TAU,**kwargs):
        super().__init__(**kwargs)
        self.w = w
        self.h = h
        self.k = k
       
        step_size = 0.01
        theta = arange(-step_size, range, step_size)

        # Parametric equation of the Fish curve
        points = [
            [
                w * cos(k * t) - h * (sin(k * t))**2,
                w * cos(k * t) * sin(k * t),
                
                0
            ] for t in theta
        ]
        if len(points) > 1:
            self.set_points_smoothly(points)

class NEMO_Animation(Scene):

    def construct(self):
        # Turning Background Transparent
        #self.camera.background_opacity = 0

        # White Background if needed
        self.camera.background_color = "#fdf6f1" 

        #Parameters
        w = 3*sqrt(2); h = 3
        p = ValueTracker(0.001)
        x = ValueTracker(0)

        #Ellipse elements
        ellipse = (
            Ellipse(width=w*2, height=h*2, color=BLUE, fill_opacity=0)
            .set_stroke(width=8, opacity=0.6)
        )
        focus = (
            Dot([3,0,0], color=GREEN)
            .set_stroke(width=12, opacity=0.4)
        )
        moving_ellipse_point = always_redraw(
                lambda: Dot(
                    [
                        w*cos(TAU * (p.get_value())),
                        h*sin(TAU * (p.get_value())),
                        0
                    ],
                    color=GREEN
                ).set_stroke(width=12, opacity=0.4)
        )
        moving_line = always_redraw(
            lambda: Line(
                start = focus.get_center(),
                end = [
                        w*cos(TAU * (p.get_value())),
                        h*sin(TAU * (p.get_value())),
                        0
                    ],
                    color=BLUE,
                ).set_stroke(width=6, opacity=0.6)
        )

        #Fish elements
        fish = always_redraw(
            lambda: Fishcurve(
                w * (1-0.125*(x.get_value()) ),
                h * (1-0.125*(x.get_value()) ),
                1,
                TAU * (p.get_value())
            ).set_stroke(color=ORANGE, width=10, opacity=1)
             .shift(UP * (2) * (x.get_value()))
        )
        moving_fish_point = always_redraw(
            lambda: Dot(
                    [
                        w * cos(TAU * (p.get_value() + 0.001)) - h * (sin(TAU * (p.get_value() + 0.001)))**2,
                        w * cos(TAU * (p.get_value() + 0.001)) * sin(TAU * (p.get_value() + 0.001)),
                        0
                    ],
                    color=GREEN,
                ).set_stroke(width=12, opacity=0.4)
        )

        moving_fish_point_DELAYED = always_redraw(
            lambda: Dot(
                    [
                        w * cos(TAU * (p.get_value()*0.01)) - h * (sin(TAU * (p.get_value()*0.01)))**2,
                        w * cos(TAU * (p.get_value()*0.01)) * sin(TAU * (p.get_value()*0.01)),
                        0
                    ],
                    color=GREEN,
                ).set_stroke(width=12, opacity=0.4)
        )

        moving_slope = always_redraw(
            lambda: Line(
                start = moving_fish_point.get_center() - (moving_fish_point.get_center() - moving_ellipse_point.get_center()) *(100/linalg.norm(moving_fish_point.get_center() - moving_ellipse_point.get_center())),
                end = moving_ellipse_point.get_center() + (moving_fish_point.get_center() - moving_ellipse_point.get_center()) *(100/linalg.norm(moving_fish_point.get_center() - moving_ellipse_point.get_center())),
                color=BLUE
            ).set_stroke(width=6, opacity=0.6) if fish.has_points() else VMobject()
        )
        
        #NEMO Text
        Nemo_text = (
            MathTex(r"\mathbb{NEMO}", font_size=200, color=BLACK)
            .set_stroke(color=BLACK, width=0.5, opacity=1)
            .shift(DOWN*2)
            
        )

        #Animating the Ellipse
        self.play(Create(ellipse), run_time=0.5)
        self.play(FadeIn(focus, moving_line, moving_ellipse_point, moving_slope), run_time=0.25)

        #Animating the Fish
        self.add(fish, focus, moving_line, moving_ellipse_point, moving_slope, moving_fish_point)
        self.play(p.animate.set_value(1), run_time=3)

        # Getting the fish to the top and Animating the Text
        self.play(FadeOut(ellipse, moving_ellipse_point, moving_line, moving_slope, moving_fish_point, focus), run_time=0.25)
        self.play(x.animate.set_value(0.6), run_time=1, rate_func=smooth)
        self.play(Write(Nemo_text), run_time=1)

        self.wait(2)
