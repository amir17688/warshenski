from GeneralEngine.constants import *
import random


class ActorSet:
    def __init__(self):
        self.actors = {}
        self.ids = 0
        self.removed_actors = 0

    def bound(self, max_x, max_y):
        self.max_x = max_x
        self.max_y = max_y

    def boundIDbyBoard(self, board):
        for ID in self.actors.keys():
            if not self.actors[ID].noclip:
                x, y = self.actors[ID].getPos()
                assert board[x][y].isTraversable(), "Actor not within traversable unit"
                vecs = self.actors[ID].getColliding()
                if VECTOR_RIGHT in vecs:
                    if not board[(x+1) % len(board)][y].isTraversable():
                        self.actors[ID].resetSubx()
                if VECTOR_LEFT in vecs:
                    if not board[(x-1) % len(board)][y].isTraversable():
                        self.actors[ID].resetSubx()
                if VECTOR_UP in vecs:
                    if not board[x][(y+1) % len(board[0])].isTraversable():
                        self.actors[ID].resetSuby()
                if VECTOR_DOWN in vecs:
                    if not board[x][(y-1) % len(board[0])].isTraversable():
                        self.actors[ID].resetSuby()

    def computeAI(self, boardObj):
        users = [self.actors[ID] for ID in self.actors.keys() if "User Controlled" in self.actors[ID].name and self.actors[ID].visible]
        user_locations = [user.getPos() for user in users]
        all_paths = []
        AIs = [self.actors[ID] for ID in self.actors.keys() if "AI Driven" in self.actors[ID].name and self.actors[ID].visible]
        for AI in AIs:
            if AI.isCentered():
                if AI.mode == "random":
                    dirs = [UP, DOWN, LEFT, RIGHT]
                    available = [boardObj.getUnit(*AI.getPos()).neighbours[index].isTraversable() for index in dirs]
                    if sum(available) == 0:
                        pass
                    elif sum(available) == 1:
                        for vec in range(len(dirs)):
                            if available[vec]:
                                AI.setDirection(VECTORS[dirs[vec]])
                    else:
                        possible = []
                        for index in range(len(dirs)):
                            if VECTORS[dirs[index]] != [-1*x for x in AI.getDirection()] and available[index]:
                                possible.append(VECTORS[dirs[index]])
                        AI.setDirection(random.choice(possible))
                elif AI.mode == "pathToUser":
                    path = boardObj.shortPath(AI.getPos(), user_locations)
                    if path is None:
                        pass
                    else:
                        AI.setDirection(getDirection(vectorSubtract(path[0][1], path[0][0])))
                        all_paths.append(path)
                        AI.cur_path = path
            else:
                if AI.cur_path != []:
                    all_paths.append([[AI.getExactPos()]+AI.cur_path[0][1:], AI.cur_path[1]])
        return all_paths

    def getCollisionCommands(self):
        all_commands = []
        keys = list(self.actors.keys())
        for ind1 in range(len(keys)):
            for ind2 in range(ind1+1, len(keys)):
                commands = self.actors[keys[ind1]].collideWith(self.actors[keys[ind2]])
                all_commands = all_commands + commands
        return all_commands

    def removeActors(self):
        self.actors = {}
        self.ids = 0

    def draw(self):
        drawings = []
        for ID in self.actors.keys():
            drawings = drawings + self.actors[ID].draw()
        return drawings

    def moveTick(self):
        for ID in self.actors.keys():
            self.actors[ID].moveTick()

    def readKeys(self, keys):
        for ID in self.actors.keys():
            if "User Controlled" in self.actors[ID].name:
                self.actors[ID].readKeys(keys)

    def addActor(self, actor):
        self.ids += 1
        self.actors[self.ids] = actor
        self.actors[self.ids].bound(self.max_x, self.max_y)
        return self.ids

    def moveActor(self, ID, x, y):
        assert 0 <= x <= self.max_x, "X-axis incorrect value {}".format(x)
        assert 0 <= y <= self.max_y, "Y-axis incorrect value {}".format(y)
        self.actors[ID].x = x
        self.actors[ID].y = y
        self.actors[ID].resetSubx()
        self.actors[ID].resetSuby()

    def allActors(self):
        return [self.actors[ID] for ID in self.actors.keys()]

    def allActorsbyName(self, name):
        return [self.actors[ID] for ID in self.actors.keys() if name in self.actors[ID].name]

    def getActor(self, ID):
        return self.actors[ID]
