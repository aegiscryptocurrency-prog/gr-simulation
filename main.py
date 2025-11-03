from vpython import *
import random
import math

# Constants
G = 6.67430e-1  # Gravitational constant (scaled for simulation)
c = 3e8  # Speed of light (for relativistic corrections)
dt = 0.01  # Time step
num_particles = 50  # Initial number of gas particles
scene = canvas(title="GR Simulation", width=800, height=600, background=color.black)

# Particle class
class Particle:
    def __init__(self, pos, vel, mass, type_):
        self.pos = vector(pos)
        self.vel = vector(vel)
        self.mass = mass
        self.type_ = type_  # 'gas', 'moon', 'planet', 'star'
        self.sphere = sphere(pos=self.pos, radius=self.get_radius(), color=self.get_color(), emissive=self.get_emissive())
        if self.type_ == 'star':
            self.light = distant_light(direction=self.pos, color=color.white)
        self.halo = sphere(pos=self.pos, radius=self.get_halo_radius(), color=color.purple, opacity=0.3, visible=False)

    def get_radius(self):
        if self.type_ == 'gas':
            return 0.1
        elif self.type_ == 'moon':
            return 0.5
        elif self.type_ == 'planet':
            return 1.0
        elif self.type_ == 'star':
            return 2.0

    def get_color(self):
        if self.type_ == 'gas':
            return color.white
        elif self.type_ == 'moon':
            return color.gray(0.5)
        elif self.type_ == 'planet':
            return color.blue
        elif self.type_ == 'star':
            return color.yellow

    def get_emissive(self):
        return self.type_ == 'star'

    def get_halo_radius(self):
        return self.get_radius() * 3

    def update_visual(self):
        self.sphere.pos = self.pos
        self.sphere.radius = self.get_radius()
        self.sphere.color = self.get_color()
        self.sphere.emissive = self.get_emissive()
        self.halo.pos = self.pos
        self.halo.radius = self.get_halo_radius()
        self.halo.visible = True
        if self.type_ == 'star':
            if hasattr(self, 'light'):
                self.light.direction = self.pos
            else:
                self.light = distant_light(direction=self.pos, color=color.white)

# Initialize particles
particles = []
for _ in range(num_particles):
    pos = vector(random.uniform(-10, 10), random.uniform(-10, 10), random.uniform(-10, 10))
    vel = vector(0, 0, 0)
    mass = random.uniform(0.1, 1.0)
    particles.append(Particle(pos, vel, mass, 'gas'))

# UI Controls
running = False
speed = 1.0

def start_simulation(b):
    global running
    running = True

start_button = button(text="Start", bind=start_simulation)

def pause_simulation(b):
    global running
    running = False

pause_button = button(text="Pause", bind=pause_simulation)

def set_speed(s):
    global speed
    speed = s.value

speed_slider = slider(min=0.1, max=50.0, value=1.0, bind=set_speed)

# Physics loop
while True:
    rate(30)
    if running:
        # Calculate forces
        forces = [vector(0,0,0) for _ in particles]
        for i in range(len(particles)):
            for j in range(len(particles)):
                if i != j:
                    r = particles[j].pos - particles[i].pos
                    dist = mag(r)
                    if dist > 0:
                        # Newtonian gravity
                        force = G * particles[i].mass * particles[j].mass / dist**2 * norm(r)
                        forces[i] += force
                        # GR precession correction (simplified)
                        v_rel = particles[i].vel - particles[j].vel
                        precession = (G * particles[j].mass / (c**2 * dist**3)) * cross(v_rel, r)
                        forces[i] += precession

        # Update velocities and positions
        for i in range(len(particles)):
            accel = forces[i] / particles[i].mass
            particles[i].vel += accel * dt * speed
            particles[i].pos += particles[i].vel * dt * speed

        # Check for coalescence
        to_merge = []
        for i in range(len(particles)):
            for j in range(i+1, len(particles)):
                dist = mag(particles[j].pos - particles[i].pos)
                if dist < particles[i].get_radius() + particles[j].get_radius():
                    to_merge.append((i, j))

        # Merge particles
        merged = set()
        for i, j in to_merge:
            if i not in merged and j not in merged:
                # Merge into larger one
                if particles[i].mass > particles[j].mass:
                    particles[i].mass += particles[j].mass
                    particles[i].vel = (particles[i].vel * particles[i].mass + particles[j].vel * particles[j].mass) / (2 * particles[i].mass)
                    particles[j].sphere.visible = False
                    particles[j].halo.visible = False
                    if hasattr(particles[j], 'light'):
                        particles[j].light.visible = False
                    merged.add(j)
                else:
                    particles[j].mass += particles[i].mass
                    particles[j].vel = (particles[j].vel * particles[j].mass + particles[i].vel * particles[i].mass) / (2 * particles[j].mass)
                    particles[i].sphere.visible = False
                    particles[i].halo.visible = False
                    if hasattr(particles[i], 'light'):
                        particles[i].light.visible = False
                    merged.add(i)

        # Remove merged particles
        particles = [p for idx, p in enumerate(particles) if idx not in merged]

        # Update types based on mass
        for p in particles:
            if p.mass > 10 and p.type_ != 'star':
                p.type_ = 'star'
            elif p.mass > 5 and p.type_ != 'planet':
                p.type_ = 'planet'
            elif p.mass > 2 and p.type_ != 'moon':
                p.type_ = 'moon'

        # Update visuals
        for p in particles:
            p.update_visual()
