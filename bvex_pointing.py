import tkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.backend_bases import key_press_handler
import numpy as np
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, solar_system_ephemeris,get_body
from astropy.time import Time
import astropy.units as u
from astropy.wcs import WCS
import matplotlib.pyplot as plt
import datetime as dt
import matplotlib.animation as animation

lat = 44.224372
lon = -76.498007
fig, ax = plt.subplots(subplot_kw={'projection': 'polar'},figsize = (20,20))

root = tkinter.Tk()
root.wm_title("BVEX pointing")

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.draw()

button = tkinter.Button(master=root, text="Quit", command=root.quit)
button.pack(side=tkinter.BOTTOM)

canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)

def make_chart(i):
    ax.clear()
    loc = EarthLocation(lon = lon*u.degree, lat = lat*u.degree)
    ra_lines = np.linspace(0,345,num = 24)
    dec_lines = np.linspace(-80,80,num = 9)
    t_utc = Time(dt.datetime.now(dt.UTC))
    lat_line_ra = np.linspace(0,360,num=1000)
    lon_line_dec = np.linspace(-90,90,num=1000)
    const_line = np.ones(1000)
    tel_frame = AltAz(location = loc, obstime=t_utc)
    for r in ra_lines:
        line = SkyCoord(ra = r*const_line*u.degree, dec = lon_line_dec*u.degree)
        line_AltAz = line.transform_to(tel_frame)
        vis = np.where(line_AltAz.alt.deg>0)
        alt = line_AltAz.alt.deg[vis]
        az = line_AltAz.az.deg[vis]
        ax.plot(az*np.pi/180, alt,'b-',alpha = 0.3)
        ax.annotate(text = str(int(r/15))+'h',xy = (az[30]*np.pi/180,alt[30]),color = "Blue",size = 16)
    for d in dec_lines:
        line = SkyCoord(ra = lat_line_ra*u.degree, dec = d*const_line*u.degree)
        line_AltAz = line.transform_to(tel_frame)
        vis = np.where(line_AltAz.alt.deg>0)
        alt = line_AltAz.alt.deg[vis]
        az = line_AltAz.az.deg[vis]
        ax.plot(az*np.pi/180, alt,'b-',alpha = 0.3)
        if(len(alt>11)):
            ax.annotate(text = str(int(d))+'$^\circ$',xy = (az[10]*np.pi/180,alt[10]),color = "Blue",size = 16)
        
        sso = ['sun','moon','mercury','venus', 'mars','jupiter','saturn', 'uranus','neptune']
    for obj in sso:
        with solar_system_ephemeris.set('builtin'):
            body = get_body(obj,t_utc,loc)
            body_AltAz = body.transform_to(tel_frame)
            body_alt = body_AltAz.alt.deg
            body_az = body_AltAz.az.deg
            if body_alt > 0:
                if(obj == 'sun'):
                    ax.plot(body_az*np.pi/180,body_alt,'yo')
                    ax.annotate('Sun',xy=((body_az+1)*np.pi/180,body_alt+1),size = 16)
                elif(obj == 'moon'):
                    ax.plot(body_AltAz.az.deg*np.pi/180,body_AltAz.alt.deg,'ko')
                    ax.annotate('Moon',xy=((body_az+1)*np.pi/180,body_alt+1),size = 16)
                else:
                    ax.plot(body_AltAz.az.deg*np.pi/180,body_AltAz.alt.deg,'k.')
                    ax.annotate(obj,xy=((body_az+1)*np.pi/180,body_alt+1),size = 16)
    
    W49N = SkyCoord(ra = '19h11m28.37s', dec='09d06m02.2s')
    W49N_AltAz=W49N.transform_to(tel_frame)
    if(W49N_AltAz.alt.deg>0):
        ax.plot(W49N_AltAz.az.deg*np.pi/180,W49N_AltAz.alt.deg,'gv')
        ax.annotate('W49N',xy = ((W49N_AltAz.az.deg+1)*np.pi/180,W49N_AltAz.alt.deg+1),size = 16)
        
    
    ax.set_rlim(90,0)  
    ax.set_rticks([80,60,40,20])
    ax.grid(True)
    ax.set_theta_zero_location("N")
    ax.tick_params(labelsize = 16)
    ax.set_title("Current Sky UTC: "+str(t_utc))

ani = animation.FuncAnimation(fig, make_chart, interval=1000)

tkinter.mainloop()
    
