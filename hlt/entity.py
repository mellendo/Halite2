import math

from . import constants
import abc
from enum import Enum
import logging
import random
import copy

Attacker = 5
Defender = 6
Explorer = 7

def nint(i) : return int(i + .5)

def getMidPos(e1, e2) :
    mid = Position(0.5*(e1.x + e2.x), 0.5*(e1.y + e2.y)) 
    mid.radius = constants.SHIP_RADIUS
    return mid

def getAngleDiff(a1, a2) :
    diff = (a1 - a2) % 360
    return diff if diff < 180 else 360 - diff

class Entity:
    """
    Then entity abstract base-class represents all game entities possible. As a base all entities possess
    a position, radius, health, an owner and an id. Note that ease of interoperability, Position inherits from
    Entity.

    :ivar id: The entity ID
    :ivar x: The entity x-coordinate.
    :ivar y: The entity y-coordinate.
    :ivar radius: The radius of the entity (may be 0)
    :ivar health: The planet's health.
    :ivar owner: The player ID of the owner, if any. If None, Entity is not owned.
    """
    __metaclass__ = abc.ABCMeta

    def _init__(self, x, y, radius, health, player, entity_id):
        self.x = x
        self.y = y
        self.radius = radius
        self.health = health
        self.owner = player
        self.id = entity_id

    def isPlanet(self) : return False
    def isShip(self)   : return False

    def zeroVel(self) :
        self.xVel = 0
        self.yVel = 0
        
    def posAfterMove(self, f) :
        return Position(self.x + f*self.xVel,self.y + f*self.yVel)

    def pos(self) :
        return self.posAfterMove(0)

    def dest(self) :
        return self.posAfterMove(1)

    def getCloseEntities(self, entities, extra) :
        close = []
        for e in entities :
            closeSqrDist = (extra + e.radius + self.radius + .1) ** 2
            if self.squareDist(e) < closeSqrDist :
                close.append(e)
        return close

    def getClosest(self, entities) :
        closest = None
        minDist = 999999
        for entity in entities :
           distance = self.calculate_distance_between(entity)
           if distance < minDist :
               closest = entity
               minDist = distance
        return closest

    def calculate_distance_between(self, target):
        """
        Calculates the distance between this object and the target.

        :param Entity target: The target to get distance to.
        :return: distance
        :rtype: float
        """
        return math.sqrt((target.x - self.x) ** 2 + (target.y - self.y) ** 2)

    def calcDist(self, target):
        return self.calculate_distance_between(target)

    def squareDist(self, target):
        """
        Calculates the square distance between this object and the target.
        """
        return (target.x - self.x) ** 2 + (target.y - self.y) ** 2

    def calculate_angle_between(self, target):
        """
        Calculates the angle between this object and the target in degrees.

        :param Entity target: The target to get the angle between.
        :return: Angle between entities in degrees
        :rtype: float
        """
        return math.degrees(math.atan2(target.y - self.y, target.x - self.x)) % 360

    def closest_point_to(self, target, min_distance=3):
        """
        Find the closest point to the given ship near the given target, outside its given radius,
        with an added fudge of min_distance.

        Puts self at target.radius + min_distance, does NOT consider self.radius

        """
        angle = target.calculate_angle_between(self)
        radius = target.radius + min_distance
        x = target.x + radius * math.cos(math.radians(angle))
        y = target.y + radius * math.sin(math.radians(angle))

        return Position(x, y)

    def randomize(self, radialDistance=3):
        """
        move randomly between min & max distance

        """
        angle = random.uniform(0,360)
        self.x += radialDistance * math.cos(math.radians(angle))
        self.y += radialDistance * math.sin(math.radians(angle))

        return self

    def getClumpTarget(self, target, targets, game_map):
        # check for anything close
        closestTarget = self.getClosest(targets)
        if not closestTarget or \
            self.calculate_distance_between(closestTarget) > \
              constants.MAX_SPEED + 1 :
            return target

        # avoid other targets
        numAtt = 3
        obsts = game_map.obstacles_between(self, target, targets)
        while obsts :
           closestObst = self.getClosest(obsts)
           if constants.DOLOG : 
               logging.info("ship {} closestObst {} target {}".format(\
                             self, closestObst, target))
           if numAtt == 0 :
               dist2cl = self.calculate_distance_between(closestObst)
               shorter = self.closest_point_to(closestObst, dist2cl - 1.61)
               if constants.DOLOG : 
                  logging.info("ship {} shorter {} target {}".format(\
                                self, shorter, target))
               return shorter
           numAtt -= 1
           points = self.closestIntegralPoints(closestObst, target)
           for point in points :
              obsts = game_map.obstacles_between(self, point, targets)
              if not obsts : return point
           obsts = game_map.obstacles_between(self, points[0], targets)
        return target

    def closestIntegralPoints(self, obst, target):
        totDist = self.calculate_distance_between(obst)
        # rounding the angle could move it by about .06
        dist2e = self.radius + obst.radius + .17
        diff = totDist - dist2e
        if diff <= 0 : return [self]
        targetDist = math.ceil(diff) + .01
        if constants.DOLOG : logging.info("ship {} obst {} totDist {} dist2e {} targetDist {}".format(\
                                           self, obst, totDist, dist2e, targetDist))
        angleOffset = math.degrees(math.acos((totDist**2 + targetDist**2 - dist2e**2) / (2 * targetDist * totDist)))
        obstAngle = self.calculate_angle_between(obst)
        targetAngle = self.calculate_angle_between(target)
        angle1 = obstAngle + angleOffset
        angle2 = obstAngle - angleOffset
        if abs(targetAngle - angle1) > abs(targetAngle - angle2) :
            angle1,angle2 = angle2,angle1
        points = []
        for angle in [angle1,angle2] :
           x = self.x + targetDist * math.cos(math.radians(angle))
           y = self.y + targetDist * math.sin(math.radians(angle))
           points.append(Position(x, y))
        return points

    def closestIntegralPoint(self, entity):
        totDist = self.calculate_distance_between(entity)
        dist2e = self.radius + entity.radius + .17
        diff = totDist - dist2e
        if diff <= 0 : return self
        targetDist = math.ceil(diff) + .01
        if constants.DOLOG : logging.info("ship {} entity {} totDist {} dist2e {} targetDist {}".format(\
                                           self, entity, totDist, dist2e, targetDist))
        angleOffset = math.degrees(math.acos((totDist**2 + targetDist**2 - dist2e**2) / (2 * targetDist * totDist)))
        angle = self.calculate_angle_between(entity) + angleOffset
        x = self.x + targetDist * math.cos(math.radians(angle))
        y = self.y + targetDist * math.sin(math.radians(angle))
        return Position(x, y)

    @abc.abstractmethod
    def _link(self, players, planets):
        pass

    def __str__(self):
        return "E-{},id={},x={},y={},r={},h={}"\
            .format(self.__class__.__name__, self.id, self.x, self.y, self.radius,self.health)

    def __repr__(self):
        return self.__str__()


class Planet(Entity):
    """
    A planet on the game map.

    :ivar id: The planet ID.
    :ivar x: The planet x-coordinate.
    :ivar y: The planet y-coordinate.
    :ivar radius: The planet radius.
    :ivar num_docking_spots: The max number of ships that can be docked.
    :ivar current_production: How much production the planet has generated at the moment. Once it reaches the threshold, a ship will spawn and this will be reset.
    :ivar remaining_resources: The remaining production capacity of the planet.
    :ivar health: The planet's health.
    :ivar owner: The player ID of the owner, if any. If None, Entity is not owned.

    """

    def __init__(self, planet_id, x, y, hp, radius, docking_spots, current,
                 remaining, owned, owner, docked_ships):
        self.id = planet_id
        self.x = x
        self.y = y
        self.radius = radius
        self.num_docking_spots = docking_spots
        self.current_production = current
        self.remaining_resources = remaining
        self.health = hp
        self.owner = owner if bool(int(owned)) else None
        self._docked_ship_ids = docked_ships
        self._docked_ships = {}
        self.zeroVel()

    def isPlanet(self) : return True

    def numDocksLeft(self) :
        return self.num_docking_spots - len(self._docked_ship_ids) 

    def get_docked_ship(self, ship_id):
        """
        Return the docked ship designated by its id.

        :param int ship_id: The id of the ship to be returned.
        :return: The Ship object representing that id or None if not docked.
        :rtype: Ship
        """
        return self._docked_ships.get(ship_id)

    def all_docked_ships(self):
        """
        The list of all ships docked into the planet

        :return: The list of all ships docked
        :rtype: list[Ship]
        """
        return list(self._docked_ships.values())

    def is_owned(self):
        """
        Determines if the planet has an owner.
        :return: True if owned, False otherwise
        :rtype: bool
        """
        return self.owner is not None

    def is_full(self):
        """
        Determines if the planet has been fully occupied (all possible ships are docked)

        :return: True if full, False otherwise.
        :rtype: bool
        """
        return len(self._docked_ship_ids) >= self.num_docking_spots

    def _link(self, players, planets):
        """
        This function serves to take the id values set in the parse function and use it to populate the planet
        owner and docked_ships params with the actual objects representing each, rather than IDs

        :param dict[int, gane_map.Player] players: A dictionary of player objects keyed by id
        :return: nothing
        """
        if self.owner is not None:
            self.owner = players.get(self.owner)
            for ship in self._docked_ship_ids:
                self._docked_ships[ship] = self.owner.get_ship(ship)

    @staticmethod
    def _parse_single(tokens):
        """
        Parse a single planet given tokenized input from the game environment.

        :return: The planet ID, planet object, and unused tokens.
        :rtype: (int, Planet, list[str])
        """
        (plid, x, y, hp, r, docking, current, remaining,
         owned, owner, num_docked_ships, *remainder) = tokens

        plid = int(plid)
        docked_ships = []

        for _ in range(int(num_docked_ships)):
            ship_id, *remainder = remainder
            docked_ships.append(int(ship_id))

        planet = Planet(int(plid),
                        float(x), float(y),
                        int(hp), float(r), int(docking),
                        int(current), int(remaining),
                        bool(int(owned)), int(owner),
                        docked_ships)

        return plid, planet, remainder

    @staticmethod
    def _parse(tokens):
        """
        Parse planet data given a tokenized input.

        :param list[str] tokens: The tokenized input
        :return: the populated planet dict and the unused tokens.
        :rtype: (dict, list[str])
        """
        num_planets, *remainder = tokens
        num_planets = int(num_planets)
        planets = {}

        for _ in range(num_planets):
            plid, planet, remainder = Planet._parse_single(remainder)
            planets[plid] = planet

        return planets, remainder


class Ship(Entity):
    """
    A ship in the game.
    
    :ivar id: The ship ID.
    :ivar x: The ship x-coordinate.
    :ivar y: The ship y-coordinate.
    :ivar radius: The ship radius.
    :ivar health: The ship's remaining health.
    :ivar DockingStatus docking_status: The docking status (UNDOCKED, DOCKED, DOCKING, UNDOCKING)
    :ivar planet: The ID of the planet the ship is docked to, if applicable.
    :ivar owner: The player ID of the owner, if any. If None, Entity is not owned.
    """

    class DockingStatus(Enum):
        UNDOCKED = 0
        DOCKING = 1
        DOCKED = 2
        UNDOCKING = 3

    def __init__(self, player_id, ship_id, x, y, hp, vel_x, vel_y,
                 docking_status, planet, progress, cooldown):
        self.id = ship_id
        self.x = x
        self.y = y
        self.owner = player_id
        self.radius = constants.SHIP_RADIUS
        self.health = hp
        self.docking_status = docking_status
        self.planet = planet if (docking_status is not Ship.DockingStatus.UNDOCKED) else None
        self._docking_progress = progress
        self._weapon_cooldown = cooldown
        self.xVel = vel_x
        self.yVel = vel_y
        self.role = None
        self.dist2Planet = None
        self.nearestPlanet = None

    def copyAttrs(self, ship) :
        self.id = ship.id
        self.owner = ship.owner
        self.health = ship.health
        self.docking_status = ship.docking_status
        self.planet = ship.planet 
        self.role = ship.role
        self.dist2Planet = ship.dist2Planet
        self.nearestPlanet = ship.nearestPlanet 

    def isAttacker(self) : return self.role == Attacker
    def isDefender(self) : return self.role == Defender
    def isExplorer(self) : return self.role == Explorer

    def isShip(self)   : return True

    def isMobile(self) : return self.docking_status == Ship.DockingStatus.UNDOCKED

    def thrust(self, magnitude, angle):
        """
        Generate a command to accelerate this ship.

        :param int magnitude: The speed through which to move the ship
        :param int angle: The angle to move the ship in
        :return: The command string to be passed to the Halite engine.
        :rtype: str
        """
        #return "t {} {} {}".format(self.id, int(magnitude), int(angle)) if int(magnitude) else None
        return "t {} {} {}".format(self.id, int(magnitude), int(angle)) 

    def dock(self, planet):
        """
        Generate a command to dock to a planet.

        :param Planet planet: The planet object to dock to
        :return: The command string to be passed to the Halite engine.
        :rtype: str
        """
        return "d {} {}".format(self.id, planet.id)

    def undock(self):
        """
        Generate a command to undock from the current planet.

        :return: The command trying to be passed to the Halite engine.
        :rtype: str
        """
        return "u {}".format(self.id)

    def getAngleForPassing(self, currAngle, entity) :
        hyp1 = self.calculate_distance_between(entity)
        opp1 = entity.radius
        angleOffset1 = math.degrees(math.asin(opp1 / hyp1))
        # rounding the angle could move it by about .06
        opp2 = self.radius + (1.17 if entity.isPlanet() else .17)
        adj = math.sqrt(hyp1**2 - opp1**2)
        angleOffset2 = math.degrees(math.atan(opp2 / adj)) 
        angleOffset = (angleOffset1 + angleOffset2) % 360
        angleToEntity = self.calculate_angle_between(entity)
        if constants.DOLOG : logging.info("hyp {} opp {} ao1 {} ao2 {} angle {} ship {} entity {}".format(\
                      hyp1 ,  opp1 ,  angleOffset1 ,angleOffset2 ,  angleToEntity,  self ,  entity ))
        angle1 = angleToEntity - angleOffset
        angle2 = angleToEntity + angleOffset
        if getAngleDiff(currAngle, angle1) < getAngleDiff(currAngle, angle2) :
           return angle1
        else :
           return angle2

    def setVels(self, target) :
        self.xVel = target.x - self.x
        self.yVel = target.y - self.y

    def truncTarget(self, target) :
        if self.calcDist(target) > 7 :
            return target.closest_point_to(self, min_distance=7.01)
        return target

    def getTarget(self, angle, distance) :
            new_target_dx = math.cos(math.radians(angle)) * distance
            new_target_dy = math.sin(math.radians(angle)) * distance
            return Position(self.x + new_target_dx, self.y + new_target_dy)

    def getFirstObst(self, target, entities) :
        self.setVels(target)
        numChecks = 15
        ncr = 1 / numChecks
        for i in range(1,numChecks+1) :
            selfIPos = self.posAfterMove(i * ncr)
            for e in entities :
                if e.id != self.id or not e.isShip() :
                    closeSqrDist = (e.radius + self.radius + .1) ** 2
                    eSqrDist = selfIPos.squareDist(e.posAfterMove(i * ncr))
                    if eSqrDist < closeSqrDist :
                        if constants.DOLOG : 
                            logging.info("gfo i {} target {} e {} ship {} ".\
                                format(i ,  target ,  e ,  self))
                        return e
        return None

    def targetIsOutsideMap(self, target, game_map) :
        return target.x < self.radius or \
               target.y < self.radius or \
               game_map.width - target.x < self.radius or \
               game_map.height - target.y < self.radius

    def target4avoidFirstObst(self, target, firstObsts, game_map) :
        obsts = game_map.obstacles_between(self, target, firstObsts)
        if obsts :
            closest = self.getClosest(obsts)
            if constants.DOLOG : logging.info("t4afo closest {} obsts {} ship {} ".format(\
                      closest, obsts, self))
            angle = nint(self.calculate_angle_between(target))
            angle = nint(self.getAngleForPassing(angle, closest))
            distance = self.calculate_distance_between(target)
            newTarget = self.getTarget(angle, distance) # TODO check this function OK
            target = copy.deepcopy(target)
            target.x = newTarget.x
            target.y = newTarget.y
        return target

    def navigate(self, target, game_map, obstLists,
                 maxSpeed=constants.MAX_SPEED, goHard=False, doFollow=False) :
        distance = int(self.calculate_distance_between(target))
        angle = nint(self.calculate_angle_between(target))
        originalAngle = angle
        firstObsts = obstLists.sitters if doFollow else obstLists.growObsts
        obsts = game_map.obstacles_between(self, target, firstObsts)
        if obsts :
            closest = self.getClosest(obsts)
            if constants.DOLOG : logging.info("n1 closest {} obsts {} ship {} ".format(\
                      closest, obsts, self))
            angle = nint(self.getAngleForPassing(angle, closest))
        if distance > maxSpeed :
            distance = maxSpeed
        target = self.getTarget(angle, distance)
        if constants.DOLOG : logging.info("n1 target {} angle {} distance {} ship {} ".format(\
                      target ,  angle ,  distance ,  self))

        if doFollow :
            closeEnts = self.getCloseEntities(obstLists.allEntities, 14)
            obstOneorMany = self.getFirstObst(target, closeEnts)
            if obstOneorMany :
               angle = nint(self.getAngleForPassing(angle, obstOneorMany))
               target = self.getTarget(angle, distance)
               if constants.DOLOG : 
                   logging.info("nf target {} angle {} distance {} ship {} ".format(\
                      target ,  angle ,  distance ,  self))
               obstOneorMany = self.getFirstObst(target, closeEnts)
        else :
            closeEnts = self.getCloseEntities(obstLists.growObsts, 7)
            obstOneorMany = game_map.obstacles_between(\
                    self, target, closeEnts)
        
        if obstOneorMany :
            target = None
            #for ao in [4, -4, 8, -8, 16, -16, 32, -32, 64, -64] :
            for ao in [4, -4, 16, -16, 64, -64 ] :
            #for ao in [2, -2, 4, -4, 8, -8, 16, -16, 32, -32, 64, -64] :
            #for ao in [8, -8, 24, -24, 72, -72 ] :
                target = self.getTarget(angle + ao, distance)
                if constants.DOLOG : logging.info("n2 target {} angle {} ao {} distance {} ship {} ".format(\
                           target ,  angle ,  ao, distance ,  self))
                if doFollow :
                    obstOneorMany = self.getFirstObst(target, closeEnts)
                else :
                    obstOneorMany = game_map.obstacles_between(\
                            self, target, closeEnts)
                if obstOneorMany :
                    target = None
                else :
                    angle = angle + ao
                    break
        if target :
            if self.targetIsOutsideMap(target, game_map) :
                if maxSpeed < 1 :
                    return None
                return self.navigate(target, game_map,  obstLists, \
                           maxSpeed = maxSpeed - 1, goHard=goHard, doFollow=doFollow) 
            #if originalAngle == angle and goHard and not doFollow :
            if originalAngle == angle and goHard :
               distance = maxSpeed
            t = self.thrust(distance, angle % 360)
            if t != None :
                self.setVels(target)
                inObstacles = obstLists.growObsts
                target.radius = self.radius
                inObstacles.append(target)   
                mid = getMidPos(target, self)
                inObstacles.append(mid)
                midS = getMidPos(mid, self)
                inObstacles.append(midS)
                midT = getMidPos(mid, target)
                inObstacles.append(midT)
                if constants.DOLOG : logging.info("n2 final target {} inObstacles ".format(\
                           target ,  inObstacles))
                return t
        self.zeroVel()
        return None

    def can_dock(self, planet):
        """
        Determine whether a ship can dock to a planet

        :param Planet planet: The planet wherein you wish to dock
        :return: True if can dock, False otherwise
        :rtype: bool
        """
        return self.calculate_distance_between(planet) <= planet.radius + constants.DOCK_RADIUS

    def _link(self, players, planets):
        """
        This function serves to take the id values set in the parse function and use it to populate the ship
        owner and docked_ships params with the actual objects representing each, rather than IDs

        :param dict[int, game_map.Player] players: A dictionary of player objects keyed by id
        :param dict[int, Planet] players: A dictionary of planet objects keyed by id
        :return: nothing
        """
        self.owner = players.get(self.owner)  # All ships should have an owner. If not, this will just reset to None
        self.planet = planets.get(self.planet)  # If not will just reset to none

    @staticmethod
    def _parse_single(player_id, tokens):
        """
        Parse a single ship given tokenized input from the game environment.

        :param int player_id: The id of the player who controls the ships
        :param list[tokens]: The remaining tokens
        :return: The ship ID, ship object, and unused tokens.
        :rtype: int, Ship, list[str]
        """
        (sid, x, y, hp, vel_x, vel_y,
         docked, docked_planet, progress, cooldown, *remainder) = tokens

        sid = int(sid)
        docked = Ship.DockingStatus(int(docked))

        ship = Ship(player_id,
                    sid,
                    float(x), float(y),
                    int(hp),
                    float(vel_x), float(vel_y),
                    docked, int(docked_planet),
                    int(progress), int(cooldown))

        return sid, ship, remainder

    @staticmethod
    def _parse(player_id, tokens):
        """
        Parse ship data given a tokenized input.

        :param int player_id: The id of the player who owns the ships
        :param list[str] tokens: The tokenized input
        :return: The dict of Players and unused tokens.
        :rtype: (dict, list[str])
        """
        ships = {}
        num_ships, *remainder = tokens
        for _ in range(int(num_ships)):
            ship_id, ships[ship_id], remainder = Ship._parse_single(player_id, remainder)
        return ships, remainder


class MegaShip(Ship):
    def __init__(self, ships, myAvg) :
        self.ships = ships
        super().__init__(None, None, myAvg.x, myAvg.y, None, None, None, None, None, None, None)
        # TODO health
        maxDist = 0
        for ship in ships :
            dist = ship.calculate_distance_between(myAvg)
            if dist > maxDist :
                maxDist = dist
        self.radius += maxDist 

    def thrust(self, magnitude, angle):
        thrusts = []
        for ship in self.ships :
            t = ship.thrust(magnitude, angle)
            if t : thrusts.append(t)
        return thrusts

    def setVels(self, target) :
        for ship in self.ships :
            ship.setVels(target)

class Position(Entity):
    """
    A simple wrapper for a coordinate. Intended to be passed to some functions in place of a ship or planet.

    :ivar id: Unused
    :ivar x: The x-coordinate.
    :ivar y: The y-coordinate.
    :ivar radius: The position's radius (should be 0).
    :ivar health: Unused.
    :ivar owner: Unused.
    """

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 0.5
        self.health = None
        self.owner = None
        self.id = None

    def _link(self, players, planets):
        raise NotImplementedError("Position should not have link attributes.")

def getAveragePos(entities) :
    sumX = 0
    sumY = 0
    num = 0
    for e in entities :
        sumX += e.x
        sumY += e.y
        num += 1
    return Position(0,0) if num == 0 else Position(sumX/num, sumY/num)
