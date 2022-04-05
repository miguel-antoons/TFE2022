#! /usr/bin/env python3
"""
geo.py

This module provides classes and functions to determine convert from GPS to ENU
coordinates.

written by Michel Anciaux, 03-May-2019
"""
import numpy as np
from numpy import sin, cos, sqrt, deg2rad
import scipy.constants as constants
import copy

C0 = constants.c
# Earth
# equatorial radius WGS-84
Ra = 6378.1370e3
# polar radius
Rb = 6356.7523142e3
# eccentricity
ecc = sqrt(1 - (Rb / Ra)**2)


def geodeticToECEF(lat, lon, h=0):
    '''
      Convert from geodetic to Earth centred Earth fixed coordinates.
      N is the prime vertical radius of curvature

      lat: latitude (rad)
      lon: longitude (rad)
      h:   altitude (m)
      return: ECEF coordinates (m)
    '''
    N = Ra / sqrt(1 - (ecc * sin(lat))**2)
    # print("N: ", N)
    x = (N + h) * cos(lat) * cos(lon)
    y = (N + h) * cos(lat) * sin(lon)
    z = ((Rb / Ra)**2 * N + h) * sin(lat)
    return np.array([x, y, z])


def ENUtoECEF(penu, lon, lat, pecef_origin=np.array((0, 0, 0))):
    '''
        Convert from local tangent plane (East-North-Up) to ECEF coordinates.
        penu: np.array(x, y, z) in ENU system (m)
        lon: latitude of local ENU origin (rad)
        lat: longitude of local ENU origin (rad)
        pecef_origin: np.array(ECEF coordinates) of local ENU origin (m)
        return: ECEF coordinates (m)

        To convert a velocity vector, leave out the pecef_origin)
    '''
    M = np.array([(-sin(lon), -sin(lat) * cos(lon), cos(lat) * cos(lon)),
                  (cos(lon), -sin(lat) * sin(lon), cos(lat) * sin(lon)),
                  (0, cos(lat), sin(lat))])
    return M.dot(penu) + pecef_origin


class GeoPos():
    ''' Position as Earth centred coordinates
        longitude and latitude in degrees, height in meters
        ground_speed in m/s, azimuth in degrees
        (North=0, positive Eastward)
    '''

    def __init__(self, latitude, longitude, height=0, name=None,
                 ground_speed=0, azimuth=0):
        lon = deg2rad(longitude)
        lat = deg2rad(latitude)
        self.lon = lon
        self.lat = lat
        self.height = height
        self.pos = geodeticToECEF(lat, lon, height)
        self.name = name
        self.vel = None
        if azimuth:
            az = deg2rad(azimuth)
            if ground_speed:
                venu = ground_speed * np.array((sin(az), cos(az), 0.0))
                self.vel = ENUtoECEF(venu, lon, lat)
        # print(self)

    def dist(self, to_geopos):
        '''
            computes the distance to another another geopos
        '''
        return sqrt(((self.pos - to_geopos.pos)**2).sum())

    def unit_vector(self, from_geopos):
        '''
            computes the unit vector from the given geopos
        '''
        vector = self.pos - from_geopos.pos
        vector /= sqrt(vector.dot(vector))
        # print("unit vector:", vector)
        return vector

    def ENU(self, ref_geopos):
        '''
            Convert from ECEF coordinates to local tangent plane (ENU)
            with origin at ref_geopos
        '''
        lon = ref_geopos.lon
        lat = ref_geopos.lat
        M = np.array([(-sin(lon), -sin(lat) * cos(lon), cos(lat) * cos(lon)),
                      (cos(lon), -sin(lat) * sin(lon), cos(lat) * sin(lon)),
                      (0, cos(lat), sin(lat))])
        M = M.transpose()
        return M.dot(self.pos - ref_geopos.pos)

    def copy(self):
        return copy.deepcopy(self)

    def __str__(self):
        s = ''
        if self.name:
            s += self.name + '\n'
        s += "\t {}\n".format(self.pos)
        if self.vel is not None:
            s += "\t {}\n".format(self.vel)
        return s


# beacon (transmitter)
BEACON = GeoPos(50.097569, 4.588487, 167, 'BEACON')


if __name__ == "__main__":
    import argparse

    def GetArguments():
        parser = argparse.ArgumentParser(
            description='''
              Convert from the GPS (WGS-84) coordinates to the East-North-Up
              coordinates relative to a reference position.
            ''')
        parser.add_argument(
            "-r", "--refpos",
            help="reference position as lat(deg) long(deg) height(m)",
            nargs=3, type=float, default=None)
        parser.add_argument(
            "pos", help="position as lat(deg) long(deg) height(m)",
            nargs=3, type=float)
        args = parser.parse_args()
        print(args)
        return args

    args = GetArguments()
    gp = GeoPos(*args.pos)
    if args.refpos is not None:
        gr = GeoPos(*args.refpos)
    else:
        gr = BEACON

    print("distance to refpos: ",gp.dist(gr))
