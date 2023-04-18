from GeneralEngine.Unit import *
import numpy as np
from GeneralEngine.BinaryHeap import BinaryHeap, Node

class Board:
    def __init__(self):
        self.initialised = False
        self.board = None

    def initialiseMapFromFile(self, filename):
        file = open(filename, "r")
        self.mapType = file.readline().split(" ")[1]
        self.mapHeight = int(file.readline().split(" ")[1])
        self.mapWidth = int(file.readline().split(" ")[1])
        assert file.readline().rstrip("\n") == "map", "Unknown map format"

        self.originalMap = [["def" for col in range(self.mapHeight)] for row in range(self.mapWidth)]

        for row in range(self.mapHeight):
            tRow = file.readline().rstrip("\n")
            for col in range(self.mapWidth):
                #Because x> y/\, [col][row]
                self.originalMap[col][self.mapHeight-row-1] = tRow[col]
        self.initialised = True
        self.resetToOriginal()

    def resetToOriginal(self):
        #Attach neighbours to each unit
        self.attachNeighbours()
        #IdentifyTurningPoints
        self.identifyTurning()
        #Generate and Attach Connections between turning points
        self.genConnections()

    def attachNeighbours(self):
        assert self.initialised, "Initialise the map from a file first!"
        for row in range(self.mapHeight):
            for col in range(self.mapWidth):
                self.stateMap[col][row].attachNeighbours([
                    self.stateMap[(col-1) % self.mapWidth][(row+1) % self.mapHeight],#Top Left
                    self.stateMap[(col  ) % self.mapWidth][(row+1) % self.mapHeight],#Top
                    self.stateMap[(col+1) % self.mapWidth][(row+1) % self.mapHeight],#Top Right
                    self.stateMap[(col+1) % self.mapWidth][(row  ) % self.mapHeight],#Right
                    self.stateMap[(col+1) % self.mapWidth][(row-1) % self.mapHeight],#Bot Right
                    self.stateMap[(col  ) % self.mapWidth][(row-1) % self.mapHeight],#Bot
                    self.stateMap[(col-1) % self.mapWidth][(row-1) % self.mapHeight],#Bot Left
                    self.stateMap[(col-1) % self.mapWidth][(row  ) % self.mapHeight] #Left
                ])

    def identifyTurning(self):
        assert self.initialised, "Initialise the map from a file first!"
        self.turningNodes = []
        for row in range(self.mapHeight):
            for col in range(self.mapWidth):
                if self.stateMap[col][row].isTraversable():
                    self.stateMap[col][row].identifyTurning()
                    if self.stateMap[col][row].isTurning():
                        self.turningNodes.append([col, row])

    def genConnections(self):
        assert self.initialised, "Initialise the map from a file first!"
        for row in range(self.mapHeight):
            for col in range(self.mapWidth):
                if self.stateMap[col][row].isTraversable():
                    self.stateMap[col][row].setTurningNeighbours(self.nearestNodes(col, row))

    def nearestNodes(self, x, y):
        assert self.turningNodes != [], "Empty turning nodes!"
        #4 Directional map
        found = [0, 0, 0, 0]
        current = [
            [(x-1) % self.mapWidth,  y    % self.mapHeight],
            [ x    % self.mapWidth, (y+1) % self.mapHeight],
            [(x+1) % self.mapWidth,  y    % self.mapHeight],
            [ x    % self.mapWidth, (y-1) % self.mapHeight],
        ]
        while 0 in found:
            for z in range(len(current)):
                if found[z] == 0:
                    if self.stateMap[current[z][0]][current[z][1]].isTraversable():
                        if current[z][0] == x and current[z][1] == y:
                            found[z] = [current[z], "y" if z%2 else "x"]
                        elif self.stateMap[current[z][0]][current[z][1]].isTurning():
                            if z == 0:
                                found[z] = [current[z], "x" if current[z][0] > x else None]
                            elif z == 1:
                                found[z] = [current[z], "y" if current[z][1] < y else None]
                            elif z == 2:
                                found[z] = [current[z], "x" if current[z][0] < x else None]
                            elif z == 3:
                                found[z] = [current[z], "y" if current[z][1] > y else None]
                    else:
                        found[z] = -1
                if found[z] == 0:
                    if z % 2 == 0:
                        current[z][0] = (current[z][0] + z - 1) % self.mapWidth
                    else:
                        current[z][1] = (current[z][1] + 2 - z) % self.mapHeight
        return found

    def getMapSize(self):
        assert self.initialised, "Initialise the map from a file first!"
        return self.mapWidth, self.mapHeight

    def getNodeConnectionCoords(self):
        coords = []
        for x, y in self.turningNodes:
            z = 0
            for turn in self.stateMap[x][y].getTurning():
                if turn != -1:
                    coords.append([(x, y), turn[0], turn[1]])
                z += 1
        return coords

    def getUnit(self, x, y):
        return self.stateMap[x][y]

    def drawCoord(self, x, y):
        return self.stateMap[x][y].Draw()

    def shortPath(self, start_coord, end_coords):
        paths = []
        start_x, start_y = start_coord
        for end in end_coords:
            end_x, end_y = end
            found = False
            if end_x == start_x and end_y == start_y:
                return None
            end_neighbour = self.stateMap[end_x][end_y].getTurning()
            start_neighbour = self.stateMap[start_x][start_y].getTurning()
            for index in range(len(end_neighbour)):
                if end_neighbour[index] != -1 and start_neighbour[index] != -1 and end_neighbour[index][0] == start_neighbour[index][0] and not found:
                    found = True
                    paths.append([[[start_x, start_y], [end_x, end_y]],self.getDist((start_x, start_y),(end_x, end_y))])
            if not found:
                end_points = [(neigh[0], self.getDist((end_x, end_y), neigh[0])) for neigh in end_neighbour if neigh != -1]
                heap = BinaryHeap()
                nid = self.coordToID(start_x, start_y)
                g_ = 0
                f_ = self.getDist((start_x, start_y), (end_x, end_y))
                heap.pool[nid] = Node(nid, g_, f_, None)
                heap.insert(nid)
                while not found and heap.size >= 0:
                    removed = heap.remove()
                    cur_x, cur_y = self.IDToCoord(removed)
                    for endTurn in end_points:
                        if endTurn[0][0] == cur_x and endTurn[0][1] == cur_y and not found:
                            cur_path = [(end_x, end_y), endTurn[0]]
                            cur_elem = heap.pool[removed]
                            dist = endTurn[1]
                            while cur_elem.prevID != None:
                                coord1 = self.IDToCoord(cur_elem.id_)
                                cur_elem = cur_elem.prevID
                                coord2 = self.IDToCoord(cur_elem.id_)
                                cur_path.append(coord2)
                                dist += self.getDist(coord1, coord2)
                            found = True
                            paths.append([cur_path[::-1], dist])
                    if not found:
                        newTurning = self.stateMap[cur_x][cur_y].getTurning()
                        for node in newTurning:
                            if node != -1:
                                nid = self.coordToID(node[0][0], node[0][1])
                                if nid not in heap.pool.keys():
                                    g_ = heap.pool[removed].g_ + self.getDist((cur_x, cur_y), node[0])
                                    f_ = g_ + min(map(lambda x: self.getDist(node[0],x[0])+x[1], end_points))
                                    heap.pool[nid] = Node(nid, g_, f_, heap.pool[removed])
                                    heap.insert(nid)
                                else:
                                    g_ = heap.pool[removed].g_ + self.getDist((cur_x, cur_y), node[0])
                                    if g_ <= heap.pool[nid].g_:
                                        heap.pool[nid].g_ = g_
                                        heap.pool[nid].f_ = g_ + min(map(lambda x: self.getDist(node[0],x[0])+x[1], end_points))
                                        heap.pool[nid].prevID = heap.pool[removed]
                                        heap.insert(nid) #Maybe update
        if paths == []:
            return None
        cur_min = paths[0]
        for x in range(1, len(paths)):
            if cur_min[1] > paths[x][1]:
                cur_min = paths[x]
        return cur_min

    def getDist(self, point1, point2):
        return np.abs(point1[0]-point2[0]) + np.abs(point1[1]-point2[1])

    def coordToID(self, x, y):
        return str(x) + "-"*(len(str(self.mapWidth))-len(str(x))) + str(y) + "-"*(len(str(self.mapHeight))-len(str(y)))

    def IDToCoord(self, ID):
        return int(ID[:len(str(self.mapWidth))].rstrip("-")), int(ID[len(str(self.mapHeight)):].rstrip("-"))
