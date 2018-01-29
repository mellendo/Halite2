"""
"""

import hlt, time
import logging
import random
import collections
import math
import copy

############################################################################

DOLOG = hlt.constants.DOLOG 

random.seed()

numFirstPlanetChosen = 0

retreatCornerShips = dict()

############################################################################
def addOppDocksToObstLists() :
    for enemyShip in oppDocks :
        if not enemyShip.isMobile() :
            obstLists.growObsts.append(enemyShip) 
            obstLists.allEntities.append(enemyShip)
            obstLists.sitters.append(enemyShip)

############################################################################
def randomBool() :
    return random.getrandbits(1)

############################################################################
class ObstLists() :
    def __init__(self) :
        pass

############################################################################
BB = 3
def getBC(z) :
    return int(z) >> BB

def getKey(e) :
    return (getBC(e.x),getBC(e.y))

def getInvKey(key) :
    return hlt.entity.Position(key[0] << BB,key[1] << BB)

class MapBlocks() :
    def __init__(self) :
        self.blocks = collections.defaultdict(list) 

    def updateBlocks(self) :
        self.blocks.clear()
        for player in game_map.all_players():
            for ship in player.all_ships():
                self.blocks[getKey(ship)].append(ship)

    def getCloseInBlocks(self,e,dist) :
        lowX = getBC(e.x - dist)
        upX  = getBC(e.x + dist) + 1
        lowY = getBC(e.y - dist)
        upY  = getBC(e.y + dist) + 1
        eX = getBC(e.x)
        eY = getBC(e.y)

        close = []
        sqrDist = dist ** 2
        for x in range(lowX,upX) :
            for y in range(lowY,upY) :
                key = (x,y)
                if True or key in self.blocks : #HACK
                    if x == eX or y == eY or \
                       x < eX and y < eY and  \
                       e.squareDist(getInvKey((x+1,y+1))) < sqrDist or \
                       x < eX and y > eY and  \
                       e.squareDist(getInvKey((x+1,y))) < sqrDist or \
                       x > eX and y < eY and  \
                       e.squareDist(getInvKey((x,y+1))) < sqrDist or \
                       x > eX and y > eY and  \
                       e.squareDist(getInvKey((x,y))) < sqrDist :
                        if DOLOG : 
                            logging.info("addKey: {} {} {}".format(\
                                    dist,e,getInvKey(key)))
                        for be in self.blocks[key] :
                            if e.squareDist(be) < sqrDist :
                                close.append(be)
                                if DOLOG : 
                                    logging.info("addToClose: {} {}".format(\
                                            e,be))
        if DOLOG : 
            logging.info("closeToE: {} close {}".format(e,close))
        return close


############################################################################
Attacker = hlt.entity.Attacker 
Defender = hlt.entity.Defender 
Explorer = hlt.entity.Explorer 

def getShipRoles() :
    for player in game_map.all_players():
        pid = player.id
        for ship in player.all_ships():
            minDist = 99999
            minPlanet = None
            for planet in game_map.all_planets():
                #if not planet.owner : continue
                d = ship.calculate_distance_between(planet) - planet.radius
                if d < minDist :
                    minDist = d
                    minPlanet = planet
            if minPlanet.owner :
                if minPlanet.owner.id != pid :
                    ship.role = Attacker
                else :
                    ship.role = Defender
            else :
                ship.role = Explorer
            ship.dist2Planet = minDist
            ship.nearestPlanet = minPlanet

############################################################################

def getMyOppHNP(totalShipHealthNProd) :
    myHNP = 0
    oppHNP = 0
    for hnpID in totalShipHealthNProd :
        if hnpID == mePlayer.id :
            myHNP += totalShipHealthNProd[hnpID]
        else :
            oppHNP += totalShipHealthNProd[hnpID]
    return myHNP, oppHNP

def logShips(game_map, ships) :
    for ship in ships :
        minDist = 99999
        for planet in game_map.all_planets():
            d = ship.calculate_distance_between(planet) - planet.radius
            if d < minDist :
                minDist = d
                minPlanet = planet
        logging.info("shipMinDist: {} ship: {} planet {}".format(minDist, ship, minPlanet))

def logGameState(game_map) :
    logging.info("turnNumber: {} ".format(turnNumber)) 

    myShipNum = len(mePlayer.all_ships())
    oppShipNum = len(game_map.oppShips())
    shipDiff = myShipNum - oppShipNum
    logging.info("shipDiff: {} my: {} opp: {}".format(shipDiff, myShipNum, oppShipNum))

    logging.info("hnpDiff: {} my: {} opp: {}".format(\
            myHNP - oppHNP, myHNP, oppHNP))

    if myShipNum + oppShipNum <= 30 :
       logging.info("myShips:")
       logShips(game_map, mePlayer.all_ships())
       logging.info("oppShips:")
       logShips(game_map, game_map.oppShips())

oppShipsPos = list()
myIdDests = list()

def recordShipInfo(game_map) :
    myIdDests.clear()
    for ship in mePlayer.all_ships() :
       myIdDests.append([ship.id, ship.dest()])

    oppShipsPos.clear()
    for ship in game_map.oppShips() :
        oppShipsPos.append(ship.pos())
        logging.info("added {} for {}".format(ship.pos(),ship))

def checkForLostShips(game_map) :
    logging.info("myIdDests {}".format(myIdDests))
    closeSqrDist = (hlt.constants.MAX_SPEED + 5 + 1 + .1) ** 2
    for idDest in myIdDests :
        if not mePlayer.get_ship(idDest[0]) :
            dest = idDest[1]
            isClose = False
            for oShip in oppShipsPos :
                logging.info("sqrDist {} closeSqrDist {} oShip {} dest {}".format(oShip.squareDist(dest), closeSqrDist, oShip, dest))
                if oShip.squareDist(dest) < closeSqrDist :
                    isClose = True
                    break
            if not isClose :
                logging.info("ERROR: idDest {} mystery gone".format(idDest))
     
############################################################################
def getDistAdd(ship, entity) :
    if not entity.isShip() :
        return 0

    oShip = entity
    if not oShip.isMobile() : 
        return -44
    #return -21
    if ship.isAttacker() :
        if oShip.isDefender() and ship.dist2Planet > oShip.dist2Planet : 
            return -31
        return -17
    if ship.isExplorer() :
        if oShip.isAttacker() :
            return -11
        return -31
    # ship is defender
    if oShip.isDefender() and ship.dist2Planet > oShip.dist2Planet : 
        return -17
    if oShip.isAttacker() and ship.dist2Planet > oShip.dist2Planet : 
        return -31 + min(20,0.5*(ship.dist2Planet - oShip.dist2Planet))

    return -31

    oShip = entity
    if not oShip.isMobile() : 
        return -34
    #return -21
    if ship.isAttacker() :
        if oShip.isDefender() and ship.dist2Planet > oShip.dist2Planet : 
            return -21
        return -14
    if ship.isExplorer() :
        if oShip.isAttacker() :
            return 7
        return -21
    # ship is defender
    if oShip.isDefender() and ship.dist2Planet > oShip.dist2Planet : 
        return 7
    if oShip.isAttacker() and ship.dist2Planet > oShip.dist2Planet : 
        return -14

    return -21

############################################################################
def nearestFirst(obj, entities) :
    dis = []
    for i in range(len(entities)) :
        dis.append([obj.calcDist(entities[i]),i])
    dis = sorted(dis)
    return [ entities[dis[i][1]] for i in range(len(entities)) ]

############################################################################
def doClumpAttack(point, closeShips) :
    myCloseShips = []
    for s in closeShips :
        isMine = s.owner.id == myID 
        if s.isMobile() :
            if not isMine :
                getTargetInfo(s.id).capacity -= 1
            elif not isCommanded(s.id) and not getShipInfo(s).isAssigned and \
                 not s.id in escapeShips :
                myCloseShips.append(s)
    clump = createClump(point)
    for s in nearestFirst(point, myCloseShips) :
        if time.time() - startTime > 1.4 :
            break 
        if DOLOG :
            logging.info("nearestFirst: {} {}".format(point,s))
        navigate_command = clump.navToClump(s)
        if navigate_command :
            addNavCmd(navigate_command)
            getShipInfo(s).isAssigned = True
            if len(clump.targets) == 1 :
                dest = s.dest()
                if DOLOG :
                    logging.info("resetCenter {} to {}".format(\
                                        clump.center,dest))
                clump.center.x = dest.x
                clump.center.y = dest.y

############################################################################
def getClosestMyDocked(e) :
    minDist = 99999
    minPlanet = None
    for p in game_map.all_planets():
        if p.owner == None or p.owner.id != mePlayer.id :
            continue
        d = e.calculate_distance_between(p) - p.radius
        if d < minDist :
            minDist = d
            minPlanet = p
    if minPlanet :
        closestDocked = e.getClosest(minPlanet.all_docked_ships())
        return closestDocked 
    return None

############################################################################
commandedShipIDs = set()

def isCommanded(sid) : return sid in commandedShipIDs

def addNavCmd(navigate_command) :
    sid = navigate_command.split()[1]
    if not sid in commandedShipIDs :
        command_queue.append(navigate_command)
        commandedShipIDs.add(sid)

############################################################################

shipID2siIndx = dict()
def getShipInfo(s) :
    return SIs[shipID2siIndx[s.id]] 

shipID2tiIndx = dict()
def getTargetInfo(sid) :
    return TIs[shipID2tiIndx[sid]] if sid in shipID2tiIndx else \
            TargetInfo(hlt.entity.Position(0,0),0)

############################################################################
def newShip(oShip, xy) :
    nShip = hlt.entity.Ship(None, None, xy[0], xy[1], None, None, None, None, None, None, None)
    nShip.copyAttrs(oShip)
    return nShip

############################################################################

def isMoving(navigate_command) :
    if not navigate_command : return False
    return navigate_command.split()[2] != 0

############################################################################

class ShipInfo():
    def __init__(self, ship) :
        self.ship = ship
        self.isAssigned = False

############################################################################

class TargetInfo():
    def __init__(self, entity, capacity, dm=1, da=0, dr=False) :
        self.entity = entity
        self.capacity = capacity
        self.distMult = dm
        self.distAdd = da
        self.doRandomize = dr
        self.targets = list()
        self.isEscape = False

############################################################################

def equalPos(p1,p2) :
    return p1.x == p2.x and p1.y == p2.y

############################################################################
class Clump :
    def __init__(self, center) :
        self.center = copy.deepcopy(center)
        self.center.radius = 5
        self.targets = []

    def navToClump(self, ship) :
        target = ship.getClumpTarget(self.center, self.targets, game_map)
        navigate_command = ship.navigate(\
                target, game_map, obstLists, doFollow=True)
        if navigate_command : 
            dest = ship.dest()
            closestTarget = dest.getClosest(self.targets + [target])
            if dest.calculate_distance_between(closestTarget) < 2.5 :
                self.targets.append(dest)
            if DOLOG: 
                logging.info(\
                    "navToClump: ship {} target {} dest {} dist {} c {}".format(\
                    ship, target, dest, dest.calcDist(target), self))
        return navigate_command 

    def __repr__(self):
        return "Clump: {} nt: {}".format(self.center, len(self.targets))

clumps = []

def createClump(center) :
    clump = Clump(center)
    clumps.append(clump)
    if DOLOG :
        logging.info("createclump: {} clumps {}".format(clump,clumps))
    return clump

def getClosestClump(fromShip, toShip) :
    centers = [ clump.center for clump in clumps ]
    obsts = game_map.obstacles_between(fromShip, toShip, centers)
    if centers :
       closestCenter = fromShip.getClosest(centers)
       for clump in clumps :
           if equalPos(closestCenter, clump.center) :
                if fromShip.calcDist(clump.center) > \
                        9.5 + math.sqrt(len(clump.targets)) :
                    return None
                else :
                    return clump
    return None

def doClump() :
   return not mildEarlyAttack and \
          mePlayer.num_ships() - 4.0 * numOppShips < 0

############################################################################
class AdvInfo() :
    def __init__(self, midPoint, distToMid=1.5) :
        self.closeShips = mbs.getCloseInBlocks(midPoint, 7 + 5 - distToMid)
        self.healthAdv = 0
        self.shipAdv = 0
        self.numCommandableShips = 0
        for s in self.closeShips :
            isMine = s.owner.id == myID 
            if DOLOG : logging.info("isMine {} myID {} s.owner {} s {}".format(\
                                     isMine, myID, s.owner.id,s))
            if s.isMobile() :
                mult = 1 if isMine else -1
                self.healthAdv += mult * s.health
                self.shipAdv += mult
                self.numCommandableShips += 1
        if DOLOG :
            logging.info(
            "adv: s {} h {} mp {} s {} oS {} cs {}".format(\
            self.shipAdv, self.healthAdv, midPoint, ship, oShip, self.closeShips))

    def lotsShips(self) :
        return self.numCommandableShips >= 3 and self.shipAdv >= 0 

    def goodForAttacker(self) :
        return self.shipAdv > 0 or self.healthAdv > 0 and self.shipAdv >= 0 or \
               self.lotsShips()

    def goodForDefender(self) :
        return self.shipAdv > 0 or self.healthAdv >= 0 and self.shipAdv == 0 or \
               self.lotsShips()
               
############################################################################
def safeToDock(ship, planet) : 
    closeShips = mbs.getCloseInBlocks(ship, 40) 
    myNum = 0
    oppNum = 0
    for s in nearestFirst(ship, closeShips) :
        if s.id != ship.id and not s.id in isDocking and s.isMobile():
            if s.owner.id == myID :
                myNum += 1
            else :
                oppNum += 1
                if myNum - oppNum < 0 :
                    return False

    return True # myNum >= oppNum * 1.1 

def myNumSitting() :
    return len(isDocking) + len(player2Docks[myID]) 

############################################################################

def doAorD(ship, target, oShip, isDefense) :
    target = ship.truncTarget(target)
    midPoint = oShip.closest_point_to(target, min_distance=1.5)
    advInfo = AdvInfo(midPoint)
    if isDefense and advInfo.goodForDefender() or \
       not isDefense and advInfo.goodForAttacker() :
        if advInfo.numCommandableShips > 1 and \
           (not probingPlanet or advInfo.numCommandableShips != advInfo.shipAdv) :
            doClumpAttack(target, advInfo.closeShips)
            return True, None
        else :
            navigate_command = ship.navigate(target, game_map,  \
                                    obstLists, doFollow=doFollow)
            return True, navigate_command 
    return False, None

############################################################################
def doDefend(ship, oShip, closestDocked, oShipDist) :
    target = closestDocked.closest_point_to(oShip, min_distance=oShipDist)
    return doAorD(ship, target, oShip, True)

############################################################################
def doAttack(ship, target, oShip) :
    return doAorD(ship, target, oShip, False)

############################################################################
def doSideAttack(ship, target1, oShip, randMult) :
    return False,None
    dx1 = target1.x - ship.x
    dy1 = target1.y - ship.y
    vecPerp = (randMult * dy1, randMult * dx1 * -1)
    vec25 = (.25 * dx1 + .75 * vecPerp[0], .25 * dy1 + .75 * vecPerp[1]) 
    # do 2 * vec25 to make sure at least distance 7
    target25 = hlt.entity.Position(ship.x + 2 * vec25[0], ship.y + 2 * vec25[1]) 
    return doAttack(ship, target25, oShip)

############################################################################

def probeDoDefend(ship, oShip) :
    #origOShip = oShip
    #goShip = guessOShip(oShip)
    closestDocked = getClosestMyDocked(oShip)
    if not closestDocked : return None
    dist2docked = oShip.calculate_distance_between(closestDocked)
    oShip = ship.target4avoidFirstObst(oShip, obstLists.sitters, game_map)
    if dist2docked < 15 :
        target = oShip.closest_point_to(closestDocked, min_distance=2)
        navigate_command = ship.navigate(target, game_map,  \
                                   obstLists, doFollow=doFollow)
    else :
        good, navigate_command = doDefend(ship, oShip, closestDocked, 3)
        if not good :
            good, navigate_command = doDefend(ship, oShip, closestDocked, 9)
        if not good :
            good, navigate_command = doDefend(ship, oShip, closestDocked, 13)
        if not good :
            target = oShip.closest_point_to(closestDocked, min_distance=2)
            navigate_command = ship.navigate(target, game_map,  \
                                        obstLists, doFollow=doFollow)
    return navigate_command 

############################################################################

def probeDoAttack(ship, entity) :
    # TODO head of the pack should become a pillager

    entity = ship.target4avoidFirstObst(entity, obstLists.sitters, game_map)
    good = False
    dist2entity = ship.calculate_distance_between(entity) - entity.radius
    if dist2entity < 9 :
        target = ship.closest_point_to(entity, min_distance=2)
        target1 = target
        good, navigate_command = doAttack(ship, target, entity)
        if not good and dist2entity < 8 and entity.isShip() and not entity.isMobile() :
            mid = hlt.entity.getMidPos(ship, entity)
            closeShips = mbs.getCloseInBlocks(mid, dist2entity / 2)
            if not game_map.obstacles_between(ship, entity, closeShips) :
                navigate_command = ship.navigate(entity, game_map,  \
                                   obstLists, goHard=True, doFollow=doFollow)
                return navigate_command 
    if not good and dist2entity > 8 :
        target = entity.closest_point_to(ship, min_distance=7.01 - 0.5)
        target1 = target
        good, navigate_command = doAttack(ship, target, entity)
    if not good and dist2entity > 4 :
        target = entity.closest_point_to(ship, min_distance=3.01 - 0.5)
        good, navigate_command = doAttack(ship, target, entity)
    if not good :
        # TODO attacker code
        # TODO try 12 away from nearest attacker toward entity, then away
        randMult = -1 if randomBool() else 1
        good, navigate_command = \
                doSideAttack(ship, target1, entity, randMult)
    if not good :
        good, navigate_command = \
                doSideAttack(ship, target1, entity, -1 * randMult)
    if not good :
        target = entity.closest_point_to(ship, min_distance=-3.01 - 0.5)
        good, navigate_command = doAttack(ship, target, entity)
    if not good :
        target = entity.closest_point_to(ship, min_distance=-7.01 - 0.5)
        good, navigate_command = doAttack(ship, target, entity)
    if not good :
        navigate_command = ship.navigate(target, game_map,  \
                            obstLists, doFollow=doFollow)
    return navigate_command 

############################################################################

shipOldXY = dict()
def guessOShip(oShip) :
    if oShip.id in shipOldXY :
        oldXY = shipOldXY[oShip.id]
        oShip = newShip(oShip, [ 2 * oShip.x - oldXY[0], 2 * oShip.y - oldXY[1] ])
    return oShip

def getMegaRunawayTarget() :
    p0 = middlePlanets[0]
    maxd = 0
    for p in middlePlanets :
        maxd = max(maxd, abs(p.x - p0.x))
        maxd = max(maxd, abs(p.y - p0.y))

    additive = max(9,p0.radius + 1.5)
    rad = maxd/2 + additive
    mcorners = []
    for x in [width/2 - rad, width/2 + rad ] :
        for y in [height/2 - rad, height/2 + rad ] :
            mcorners.append(hlt.entity.Position(x,y))

    ncorners = []
    for mc in nearestFirst(myAvg, mcorners) :
        if myAvg.calcDist(mc) > 7 :
            ncorners.append(mc)
            if len(ncorners) == 2 :
                break

    tncorners = [ship.truncTarget(nc) for nc in ncorners]
    cornerNearOpp = nearestFirst(nearestOppAvg, tncorners)
    if DOLOG :
        logging.info("EarlyRunTarget: t: {} tnc: {} n: {} m: {} mya: {} noa: {}".format( \
                    cornerNearOpp[-1],tncorners,ncorners,mcorners,myAvg,nearestOppAvg))

    return cornerNearOpp[-1]

def moveEarlyMegaShip(oShip, game_map, myAvg, command_queue) :
    mePlayer = game_map.get_me()
    earlyMegaShip = hlt.entity.MegaShip(mePlayer.all_ships(), myAvg)
    # TODO distance depends on isMobile()
    if oShip.isMobile() :
        randDist = random.uniform(3,7)
        target = ship.closest_point_to(oShip, min_distance = randDist + earlyMegaShip.radius)
        dist = ship.calculate_distance_between(oShip)
        if dist < 23 :
            if numActualOpps == 1 and \
               myHNP >= totalShipHealthNProd[nearestOppID] :
                target = getMegaRunawayTarget()
        elif dist < 19 :
            target.randomize()
            dist = target.calculate_distance_between(oShip)
            if dist < 0.6 + 0.1 + earlyMegaShip.radius : # don't crash
                target = ship.closest_point_to(oShip, min_distance = \
                        randDist + earlyMegaShip.radius)
    else :
        target = ship.closest_point_to(oShip, min_distance = 2 + (earlyMegaShip.radius - .5))

    obstLists = ObstLists()
    obstLists.growObsts = list(game_map.all_planets())
    obstLists.allEntities = list(game_map.all_planets())
    obstLists.sitters = list(game_map.all_planets())

    navigate_command = earlyMegaShip.navigate(target, game_map, obstLists)
    if navigate_command :
        command_queue += navigate_command 

############################################################################

didEarlyMegaShip = False
def doEarlyAttackManeuvers(oShip, game_map, myAvg, command_queue, obstLists) :
    global didEarlyMegaShip 
    if oShip.isMobile() :
        if not didEarlyMegaShip :
            # find ship closest to myAvg and see if MegaShip is complete
            minDist = 99999
            maxDist = 0
            avgShip = None
            for ship in mePlayer.all_ships():
                dist = ship.calculate_distance_between(myAvg)
                if dist < minDist :
                    minDist = dist
                    avgShip = ship
                if dist > maxDist :
                    maxDist = dist
            if maxDist < 2 * avgShip.radius + .5 :
                didEarlyMegaShip = True
            if DOLOG :
                logging.info("MegaShipping: {} {} ships: {}".format( \
                    didEarlyMegaShip, maxDist, mePlayer.all_ships()))
    
        if not didEarlyMegaShip :
            # move other ships toward avgShip
            for ship in mePlayer.all_ships():
                if avgShip != ship :
                    navigate_command = ship.navigate(ship.closestIntegralPoint(avgShip),
                            game_map,  obstLists)
                    if isMoving(navigate_command) :
                        addNavCmd(navigate_command)

        if not command_queue :
            didEarlyMegaShip = True
            moveEarlyMegaShip(oShip, game_map, myAvg, command_queue)
    else :
        if not didEarlyMegaShip :
            return False
        else :
            moveEarlyMegaShip(oShip, game_map, myAvg, command_queue)

    if DOLOG : logging.info("MegaShippingCommand: {}".format(command_queue))

    return True

############################################################################

RetreatingState         = 0
ClockwiseState          = 1
CounterClockwiseState   = 2
id2retreatState = collections.defaultdict(int) 

ONTOP    = 0
ONLEFT   = 1
ONBOTTOM = 2
ONRIGHT  = 3

def getSidePos(e) :
    DRs = [ [ e.y , ONTOP    ], 
            [ e.x , ONLEFT   ],
            [ height - e.y , ONBOTTOM ], 
            [ width  - e.x , ONRIGHT  ] ]
    return sorted(DRs)[0][1]

def getRetreatPoint() :
        mPos = getSidePos(myAvg)
        if mPos == ONTOP :
           rp = hlt.entity.Position(myAvg.x,2)
        if mPos == ONLEFT   :
           rp = hlt.entity.Position(2, myAvg.y)
        if mPos == ONBOTTOM :
           rp = hlt.entity.Position(myAvg.x,height - 2)
        if mPos == ONRIGHT  :
           rp = hlt.entity.Position(width - 2, myAvg.y)
        return rp

def getRevolvingTarget(ship, shipState, pos) :
    DTN = .5
    if shipState == CounterClockwiseState :
        if pos == ONTOP :
            target = hlt.entity.Position(ship.x - 7, 2.2)
            if target.x < DTN :
                return getRevolvingTarget(ship, shipState, ONLEFT)
        if pos == ONLEFT :
            target = hlt.entity.Position(2.2, ship.y + 7)
            if target.y > height - DTN :
                return getRevolvingTarget(ship, shipState, ONBOTTOM)
        if pos == ONBOTTOM :
            target = hlt.entity.Position(ship.x + 7, height - 2.2)
            if target.x > width - DTN :
                return getRevolvingTarget(ship, shipState, ONRIGHT)
        if pos == ONRIGHT :
            target = hlt.entity.Position(width - 2.2, ship.y - 7)
            if target.y < DTN :
                return getRevolvingTarget(ship, shipState, ONTOP)
    else :
        if pos == ONTOP :
            target = hlt.entity.Position(ship.x + 7, 3.4)
            if target.x > width - DTN :
                return getRevolvingTarget(ship, shipState, ONRIGHT)
        if pos == ONLEFT :
            target = hlt.entity.Position(3.4, ship.y - 7)
            if target.y < DTN :
                return getRevolvingTarget(ship, shipState, ONTOP)
        if pos == ONBOTTOM :
            target = hlt.entity.Position(ship.x - 7, height - 3.4)
            if target.x < DTN :
                return getRevolvingTarget(ship, shipState, ONLEFT)
        if pos == ONRIGHT :
            target = hlt.entity.Position(width - 3.4, ship.y + 7)
            if target.y > height - DTN :
                return getRevolvingTarget(ship, shipState, ONBOTTOM)

    return target

############################################################################

def getClosestDist(target,enemyShips) :
    closest = target.getClosest(enemyShips)
    return 99999 if closest == None else target.calcDist(closest)

def retreatNavigate(ship, target, doClump=True) :
    target = ship.target4avoidFirstObst(target, obstLists.sitters, game_map)
    target = ship.truncTarget(target)
    enemyShips = []
    for s in mbs.getCloseInBlocks(ship, 41) :
        if s.owner.id != myID and s.isMobile() : enemyShips.append(s)
    dist = getClosestDist(target, enemyShips)
    if DOLOG: logging.info("retreatNav {} dist {} {}".format(\
                     ship, dist, enemyShips))
    if dist < 15 :
        numAngles = 32
        targets = [ship]
        for i in range(numAngles) :
            target = ship.getTarget(i * 360 / numAngles, 7.01)
            if ship.targetIsOutsideMap(target, gm) :
                continue
            if gm.obstacles_between(ship, target, gm.all_planets()) :
                continue
            targets.append(target)

        DTs = []
        for i in range(len(targets)) :
            DTs.append([getClosestDist(targets[i], enemyShips),i])
        dt = sorted(DTs)[-1]
        dist = dt[0]
        target = targets[ dt[1] ]
        if DOLOG: logging.info("retreatNav dist {} t {} DTs {} {}".format(\
                     dist, target, DTs, targets))

    if doClump :
        doClumpAttack(target, mbs.getCloseInBlocks(target, 8)) 
        return None

    navigate_command = ship.navigate(target, game_map,  \
                                     obstLists, doFollow=True)
    return navigate_command 

############################################################################

doRetreat = False
retreatPoint = None
def checkDoMassRetreat(SIs) :
    if numActualOpps == 1 :
        return 

    global doRetreat
    if not doRetreat :
        if DOLOG: logging.info("myNShips {} mvAvgNS {}".format(\
                     mePlayer.num_ships(), mvAvgNumShips[myID]))
        if mePlayer.num_ships() >= mvAvgNumShips[myID] or \
           len(player2histShips[myID]) < 10 :
            return
    
        #if lowerID != None : # a player with less hist ships and some docked 
        #if True :
            #if mePlayer.num_ships() < 10 and len(player2histShips[myID])  > 30 :
                #doRetreat = True
    
        #sortedHist = list()
        #for player in gm.all_players() :
            #sortedHist.append([len(player2histShips[player.id]),player.id])
        #sortedHist = sorted(sortedHist)
        #for i in range(len(sortedHist)) :
            #if myID == sortedHist[i][1] :
                #mySHIdx = i
                #break

        #if DOLOG: logging.info("mySHIdx {} sortedHist {}".format(\
                     #mySHIdx, sortedHist))

        #if mySHIdx == len(sortedHist) - 1 :
            #return

        #upperPlayer = gm.get_player(sortedHist[mySHIdx + 1][1])
        #divisor = 2
        #if mePlayer.num_ships() < upperPlayer.num_ships() / divisor :
            #doRetreat = True

        sortedNS = list()
        for player in gm.all_players() :
            if len(player2Docks[player.id]) > 0 :
                sortedNS.append([player.num_ships(),player.id])
        sortedNS = sorted(sortedNS)
        mySNSIdx = None
        for i in range(len(sortedNS)) :
            if myID == sortedNS[i][1] :
                mySNSIdx = i
                break

        if DOLOG: logging.info("mySNSIdx {} sortedNS {}".format(\
                     mySNSIdx, sortedNS))
    
        if mySNSIdx == None : # we haven't docked yet.
            return 

        if mySNSIdx == len(sortedNS) - 1 : # We are the best
            return
        if len(sortedNS) == 1 : # only us with docked ships
            return
    
        upperPlayer = gm.get_player(sortedNS[mySNSIdx + 1][1])
        if mePlayer.num_ships() < upperPlayer.num_ships() / (2 + mySNSIdx) or \
           mePlayer.num_ships() < myMaxNumShips / 2 and \
           len(player2Mobiles[myID]) <= 7 :
            doRetreat = True
    
    if not doRetreat : 
        return

    global retreatPoint 
    if retreatPoint == None :
        retreatPoint = getRetreatPoint()

    escapeShips.clear()
    retreatCornerShips.clear()
    if len(retreatCornerShips) == 0 :
        mobiles = set(player2Mobiles[myID])
        for cp in nearestFirst(myAvg, cornerPoints) :
            if len(mobiles) > 0 :
                mobile = cp.getClosest(
                            [mePlayer.get_ship(mid) for mid in mobiles])
                retreatCornerShips[mobile.id] = cp
                mobiles.discard(mobile.id)
                
    if DOLOG: logging.info("retreatPoint {} ".format(retreatPoint ))

    addOppDocksToObstLists()

    DSIs = []
    for i in range(len(SIs)) :
        si = SIs[i]
        DSIs.append([getClosestDist(si.ship, cornerPoints),i])

    for dsi in sorted(DSIs) :
        si = SIs[dsi[1]]
        if time.time() - startTime > 1.4 :
            break 

        ship = si.ship
        if ship.id in escapeShips or si.isAssigned :
            continue

        navigate_command = None
        shipState = id2retreatState[ship.id]
        pos = getSidePos(ship)
        if shipState == RetreatingState :
            target = retreatPoint 
            if ship.calculate_distance_between(target) < 7 :
                if pos == ONLEFT   and ship.y > target.y or \
                   pos == ONTOP    and ship.x < target.x or \
                   pos == ONRIGHT  and ship.y < target.y or \
                   pos == ONBOTTOM and ship.x > target.x :
                    shipState = CounterClockwiseState
                else :
                    shipState = ClockwiseState

        id2retreatState[ship.id] = shipState 

        if shipState != RetreatingState :
            target = getRevolvingTarget(ship, shipState, pos)

        if ship.id in retreatCornerShips :
            target = retreatCornerShips[ship.id]

        navigate_command = retreatNavigate(ship, target, doClump = False) 

        if DOLOG: logging.info("retreatPt {} target {} nc {} ship {}".format(\
                retreatPoint, target, navigate_command, ship))
        
        if navigate_command:
            addNavCmd(navigate_command)
        si.isAssigned = True

############################################################################

game = hlt.Game('mellendo59')

hasDocked = False
firstPlanetID = None
doFirstPlanetID = None

command_queue = []
TIs = []
DIs = []
SIs = []

escapePoints = []
doEscapePoint = True
escapeShips = set()

turnNumber = -1
oppDockedAt = None 

player2histShips = collections.defaultdict(set) 
player2histDocks = collections.defaultdict(set) 
mvAvgNumShips = dict()
myMaxNumShips = 0

circleRadius = 10
circleAngle = 0
numCirclePoints = int(random.uniform(2,10))
#numCirclePoints = 4
circleSpin = random.uniform(6,10)
#circleSpin = 2
circleDoRandomize = False

mbs = MapBlocks()

probingPlanet = False
isDocking = set()
                       
wait33 = None

# MAIN LOOP

while True:
    # Update the map for the new turn and get the latest version
    game_map = game.update_map()
    gm = game_map 
    startTime = time.time()
    mbs.updateBlocks()

    width = game_map.width
    height = game_map.height

    cornerPoints = [hlt.entity.Position(1,1), \
                    hlt.entity.Position(width-1,1), \
                    hlt.entity.Position(1,height-1), \
                    hlt.entity.Position(width-1,height-1) ]

    turnNumber += 1
    mePlayer = game_map.get_me()
    myID = mePlayer.id

    isDocking.clear()

    totalShipHealthNProd = game_map.getTotalShipHealthNProdDict()
    myHNP, oppHNP = getMyOppHNP(totalShipHealthNProd)

    numStrongOpps = game_map.numStrongOpps()
    numActualOpps = game_map.numActualOpps()

    getShipRoles()

    if DOLOG :
        logGameState(game_map)
        checkForLostShips(game_map)

############################################################################
    for player in game_map.all_players():
        pid = player.id
        if pid in mvAvgNumShips :
            mvAvgNumShips[pid] += .14 * (player.num_ships() - mvAvgNumShips[pid])
        else :
            mvAvgNumShips[pid] = player.num_ships()

    myMaxNumShips = max(myMaxNumShips, player.num_ships())

############################################################################
    myAvg = hlt.entity.getAveragePos(mePlayer.all_ships())
    allOppAvg = hlt.entity.getAveragePos(game_map.oppShips())
    oppAvg = dict()
    closestOppDist = 99999
    for player in game_map.all_players():
        if player.num_ships() > 0 and player.id != mePlayer.id :
            oppAvg[player.id] = hlt.entity.getAveragePos(player.all_ships())
            oppDist = myAvg.calculate_distance_between(oppAvg[player.id]) 
            if oppDist < closestOppDist :
                nearestOppID = player.id
                nearestOpp = player
                closestOppDist = oppDist 
                nearestOppAvg = oppAvg[nearestOppID]
    
    #basePoint = hlt.entity.Position(2*myAvg.x - allOppAvg.x,2*myAvg.y - allOppAvg.y)
    baseX = 0 if myAvg.x < game_map.width / 2 else game_map.width
    basePoint = hlt.entity.Position(baseX, game_map.height / 2)
    centerPoint = hlt.entity.Position(game_map.width / 2, game_map.height / 2)

    if hlt.constants.DOLOG : logging.info("myAvg {} allOppAvg {} basePoint {} centerPoint {}".format(\
                      myAvg ,  allOppAvg ,  basePoint, centerPoint ))

############################################################################
    
    if doFirstPlanetID == None :
        i = 0
        doFirstPlanetID = (numActualOpps == 1)
        for planet in nearestFirst(centerPoint, game_map.all_planets()) :
            i += 1
            if planet.num_docking_spots >= 3 and i > 4 :
                doFirstPlanetID = True
                break
        if not doFirstPlanetID :
            logging.info("no doFirstPlanetID {}".format(centerPoint))

############################################################################

    middlePlanets = []
    outerPlanets = []
    i = 0
    for planet in nearestFirst(centerPoint, game_map.all_planets()) :
        i += 1
        if i > 4 :
            outerPlanets.append(planet)
        else :    
            middlePlanets.append(planet)

############################################################################
    if not escapePoints and game_map.losingBig() and numActualOpps > 1 \
        and len(player2histShips[mePlayer.id]) > 20 and doEscapePoint :
        x = game_map.width - .5 if 2 * myAvg.x > game_map.width else .5
        y = game_map.height - .5 if 2 * myAvg.y > game_map.height else .5
        escapePoints.append(hlt.entity.Position(x, y))
        #escapePoints.append(getRetreatPoint())

    # Here we define the set of commands to be sent to the Halite engine at the end of the turn
    command_queue.clear()
    commandedShipIDs.clear()
############################################################################

    oppDocks = set()
    player2Mobiles = collections.defaultdict(set) 
    player2Docks = collections.defaultdict(set) 
    for player in game_map.all_players():
        for ship in player.all_ships():
            player2histShips[player.id].add(ship.id)
            if ship.isMobile() :
                player2Mobiles[player.id].add(ship.id)
            else :
                player2histDocks[player.id].add(ship.id)
                player2Docks[player.id].add(ship.id)
                if player.id != game_map.my_id :
                    oppDocks.add(ship)

    numOppMobiles = 0
    numOppShips = 0
    for player in game_map.all_players():
        if player.id != game_map.my_id :
           numOppMobiles += len(player2Mobiles[player.id])
           numOppShips += player.num_ships()

    extraMobiles = len(player2Mobiles[mePlayer.id]) - 2 * numOppMobiles 
    extraShips = mePlayer.num_ships() - 2 * numOppShips

############################################################################
    circlePoints = []
    circleCapacity = extraMobiles // numCirclePoints
    if len(player2histShips) >= 5 and circleCapacity > 0 and extraShips > 0 :
        circleRadius += 0.8
        # 360 moves 6 * r, so 360 * 2.5 / (6 * r) moves 2.5
        circleAngle += 360 * circleSpin / (numCirclePoints * circleRadius)
        for i in range(numCirclePoints) :
            ira = math.radians(circleAngle + i * 360 / numCirclePoints)
            x = game_map.width/2  + circleRadius * math.cos(ira)
            y = game_map.height/2 + circleRadius * math.sin(ira)
            circlePoints.append(hlt.entity.Position(x,y))

############################################################################

    isEarly = (len(player2histShips[mePlayer.id]) <= 4 and \
               len(player2histDocks[nearestOppID]) < 3)
    hugeEarlyAttack = False
    mildEarlyAttack = False
    numEarlyClose = 0
    numEarlyReallyClose = 0
    if len(player2Docks[nearestOppID]) == 0 :
        oppDockedAt = None
    numOppDockedTurns = 0 if oppDockedAt == None else turnNumber - oppDockedAt 
    earlyDist = 62 - hlt.constants.MAX_SPEED * numOppDockedTurns * \
                     len(player2Docks[nearestOppID]) / 3

    if isEarly :
        hugeEarlyAttack = True
        for player in game_map.all_players():
            if player.id == nearestOppID :
                for oShip in player.all_ships():
                    if not oppDockedAt and not oShip.isMobile() :
                        oppDockedAt = turnNumber 
                    for mShip in mePlayer.all_ships() :
                        dist = mShip.calculate_distance_between(oShip)
                        if dist > earlyDist :
                            hugeEarlyAttack = False
                        else :
                            mildEarlyAttack = True
                    if not oShip.isMobile() :
                        hugeEarlyAttack = False
                    for mShip in mePlayer.all_ships() :
                        dist = mShip.calculate_distance_between(oShip)
                        if oShip.isMobile() :
                            if dist < (84 if numActualOpps > 1 else 96) :
                                numEarlyClose += 1
                            if dist < 61 :
                                numEarlyReallyClose += 1
                        break

    myNumShips = mePlayer.num_ships()
    myNumMobiles = myNumShips - myNumSitting() 

    myNumCanDock = myNumMobiles - numEarlyClose 
    myNumMustUndock = numEarlyReallyClose - myNumMobiles
    if (numEarlyReallyClose == 3 and myNumShips == 4) :
        myNumMustUndock = 4

    if mildEarlyAttack :
        firstPlanetID = None

    doFollow = mildEarlyAttack or hasDocked

############################################################################
    numPlanetsToLeave = 4 if numActualOpps > 1 else 0
    numPlanetsToLeave = 0 
    numNotMine = 0
    for planet in game_map.all_planets():
        if not planet.owner or planet.owner.id != mePlayer.id :
            numNotMine += 1

############################################################################

    TIs.clear()
    shipID2tiIndx.clear()
    for planet in game_map.all_planets():
        docksLeft = planet.numDocksLeft()
        # If the planet is owned
        if docksLeft == 0 and planet.owner == mePlayer :
            # Skip this planet
            continue

        distMult = 1.0 # / planet.num_docking_spots 
        if planet.owner == mePlayer or planet.owner == None :
            #ti = TargetInfo(planet, docksLeft, dm=1)
            ti = TargetInfo(planet, docksLeft, dm=distMult, \
                            da=-(planet.radius + 2*planet.num_docking_spots))
            TIs.append(ti)
        else :
            #TIs.append(TargetInfo(planet, 999, dm=numStrongOpps))
            TIs.append(TargetInfo(planet, 999, dm=distMult, da=999))
            TIs.append(TargetInfo(planet, planet.num_docking_spots, dm=distMult, da=-planet.radius))

    for ep in escapePoints :
        ti = TargetInfo(ep, 1, da=-99999)
        ti.isEscape = True
        TIs.append(ti)

    for cp in circlePoints :
        TIs.append(TargetInfo(cp, circleCapacity, dr=circleDoRandomize))

    for player in game_map.all_players():
        if time.time() - startTime > 0.3 :
            break 
        if player.id != game_map.my_id :
            if len(player2histDocks[player.id]) > 0 and \
               len(player2Docks[player.id]) == 0 and hasDocked : 
                # TODO consider also checking if near my docked ships
                continue
            for targetShip in player.all_ships():
                da = 0
                #da = (-20 if targetShip.isMobile() or numStrongOpps < 2 else -3)
                #if numActualOpps == 1 :
                    #da = (-20 if targetShip.isMobile() else -20)
                    #da = (-20 if targetShip.isMobile() else -34)
                # TODO go after players in order of ships produced
                if numNotMine <= numPlanetsToLeave and \
                   not targetShip.isMobile() :
                    da += 9999
                shipID2tiIndx[targetShip.id] = len(TIs)
                TIs.append(TargetInfo(targetShip, 
                    999 if numNotMine <= numPlanetsToLeave else
                    1 if targetShip.isMobile() else 
                    2, da = da)) 
                if not hasDocked and player.id == nearestOppID and mildEarlyAttack :
                   da -= earlyDist 
                   if not targetShip.isMobile() :
                      da -= earlyDist 
                   TIs.append(TargetInfo(targetShip, 1, da = da)) 
                   #TIs.append(TargetInfo(targetShip, 2, da = 9999)) 

############################################################################

    obstLists = ObstLists()
    obstLists.growObsts = mePlayer.all_ships() + game_map.all_planets()
    if mildEarlyAttack :
        obstLists.growObsts += nearestOpp.all_ships()
    obstLists.allEntities = mePlayer.all_ships() + game_map.all_planets()
    obstLists.sitters = list(game_map.all_planets())

############################################################################

    SIs.clear()
    shipID2siIndx.clear()
    for ship in mePlayer.all_ships():
        if time.time() - startTime > 0.5 :
            break 
        # If the ship is docked
        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            # Skip this ship
            obstLists.sitters.append(ship)
            if myNumMustUndock > 0 :
                myNumMustUndock -= 1
                addNavCmd(ship.undock())
            continue

        shipID2siIndx[ship.id] = len(SIs)
        SIs.append(ShipInfo(ship))

############################################################################
    checkDoMassRetreat(SIs)

############################################################################

    DIs.clear()
    for tii in range(len(TIs)):
        if time.time() - startTime > 0.7 :
            break 
        ti = TIs[tii]
        entity = ti.entity
        baseFrac = max(0, 0.75 * ((numStrongOpps - 1) / 2))
        cf = .35 + .15 * (middlePlanets[0].num_docking_spots - 3)
        centerFrac = max(0, cf * ((1.5 - numStrongOpps) * 2))
        #tiAdd = entity.calculate_distance_between(basePoint) * baseFrac + \
        tiAdd = abs(entity.x - basePoint.x) * baseFrac + \
                entity.calculate_distance_between(centerPoint) * centerFrac 
        for sii in range(len(SIs)):
            ship = SIs[sii].ship
            da = getDistAdd(ship, entity)
            realDist = ship.calculate_distance_between(entity) 
            dist = realDist * ti.distMult + ti.distAdd + tiAdd + da
            DIs.append([dist, sii, tii, realDist])

############################################################################
    clumps.clear() 
    for di in sorted(DIs) :
        if time.time() - startTime > 1.4 :
            break 
        si = SIs[di[1]]
        ti = TIs[di[2]]
        realDist = di[3]
        if si.isAssigned or ti.capacity <= 0 :
            continue

        navigate_command = None
        ship = si.ship
        if ti.entity.isPlanet() :
           planet = ti.entity

           if mildEarlyAttack or \
              numNotMine <= numPlanetsToLeave and planet.owner != mePlayer :
               continue

           if len(player2histShips[mePlayer.id]) <= 3 and doFirstPlanetID :
               if firstPlanetID == None :
                   if ti.capacity < 3 :
                       continue
                   firstPlanetID = planet.id
               elif firstPlanetID != planet.id :
                   continue

           #owner check superfluous
           # TODO Need to check if we have support for docking
           if ship.can_dock(planet) and (planet.owner == mePlayer or planet.owner == None) : 
               if not safeToDock(ship, planet) : 
                   continue
               if myNumCanDock > 0 : 
                   myNumCanDock -= 1
               else : 
                   skipPlanet = True
                   if numEarlyClose == 3 and myNumShips == 3 :
                       if wait33 == None :
                           wait33 = turnNumber + 5
                       if turnNumber < wait33 :
                           #si.isAssigned = True
                           skipPlanet = False
                   if skipPlanet :
                       continue
               addNavCmd(ship.dock(planet))
               if planet.owner == None :
                   numNotMine -= 1
               si.isAssigned = True
               isDocking.add(ship.id)
               hasDocked = True
               ti.capacity -= 1
           else:
               if planet.owner == mePlayer or planet.owner == None :
                   probingPlanet = True
                   navigate_command = probeDoAttack(ship, planet)
                   probingPlanet = False
               else : 
                   closestDocked = ship.getClosest(planet.all_docked_ships())
                   navigate_command = probeDoAttack(ship, closestDocked)

        elif ti.entity.isShip() :

            oShip = ti.entity

            if hugeEarlyAttack and realDist < 6 * hlt.constants.MAX_SPEED and not command_queue :
                if doEarlyAttackManeuvers(oShip, game_map, myAvg, command_queue, obstLists) :
                   break

            didEarlyMegaShip = False

            #closeClump = getClosestClump(ship, oShip) 
            closeClump = None

            if mildEarlyAttack :
                if oShip.isMobile() :
                    navigate_command = ship.navigate(oShip, game_map,  \
                                            obstLists, doFollow=True)
                else :
                    target = ship.closest_point_to(oShip, min_distance=2)
                    navigate_command = ship.navigate(target, game_map,  \
                                            obstLists, doFollow=True)
            elif oShip.isMobile() :
                #if ship.isAttacker() or 
                   #ship.dist2Planet > entity.dist2Planet : 
                    #continue
                if oShip.isAttacker() or ship.isDefender() :
                    # and (not oShip.isDefender() or 
                    # ship.dist2Planet < entity.dist2Planet : 
                    navigate_command = probeDoDefend(ship, oShip)
                elif ship.isAttacker() and oShip.isDefender() :
                    closestDocked = ship.getClosest(oShip.nearestPlanet.all_docked_ships())
                    navigate_command = probeDoAttack(ship, closestDocked)
                else :
                    navigate_command = probeDoAttack(ship, oShip)
            else :
                navigate_command = probeDoAttack(ship, oShip)
        else :
            target = ti.entity
            if ti.doRandomize : target = copy.deepcopy(target).randomize(7)
            target = ship.getClumpTarget(target, ti.targets, game_map)
            navigate_command = retreatNavigate(ship, target, doClump=False)
            if navigate_command : 
                if ti.isEscape :
                    escapeShips.add(ship.id)
                dest = ship.dest()
                closestTarget = dest.getClosest(ti.targets + [target])
                if dest.calculate_distance_between(closestTarget) < 2.5 :
                   ti.targets.append(dest)
 
        if navigate_command:
            addNavCmd(navigate_command)
            ti.capacity -= 1
        si.isAssigned = True

    if DOLOG :
        logging.info("command_queue: {} ".format(command_queue)) 
        recordShipInfo(game_map)

    # Send our set of commands to the Halite engine for this turn
    game.send_command_queue(command_queue)

    shipOldXY.clear()
    for player in game_map.all_players():
        if player.id != game_map.my_id :
            for oShip in player.all_ships():
               shipOldXY[oShip.id] = [oShip.x, oShip.y]

    # TURN END
# GAME END
