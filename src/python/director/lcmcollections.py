import director.vtkAll as vtk
import director.objectmodel as om
from director import lcmUtils

# if bot_lcmgl cannot be important than this module will not be able to
# support lcmgl, but it can still be imported in a disabled state
try:
    import bot_lcmgl
    import vs as lcmCollections
    LCMGL_AVAILABLE = True
except ImportError:
    LCMGL_AVAILABLE = False


class CollectionInfo():
    def __init__(self, collectionId, collectionName, collectionType, collectionShow):
        self.id =   collectionId
        self.name = collectionName
        self.type = collectionType
        self.show = collectionShow


class CollectionInfoObject(om.ObjectModelItem):

    def __init__(self, collectionInfo, actor):

        om.ObjectModelItem.__init__(self, collectionInfo.name, om.Icons.Robot)

        self.actor = actor
        self.collectionInfo = collectionInfo
        #self.actor.SetUseBounds(False)
        self.addProperty('Visible', actor.GetVisibility())
        self.views = []

    def _onPropertyChanged(self, propertySet, propertyName):
        om.ObjectModelItem._onPropertyChanged(self, propertySet, propertyName)

        if propertyName == 'Visible':
            makeVisible = self.getProperty(propertyName)
            self.actor.SetVisibility(makeVisible)
            print "doing visible", makeVisible
            print self.collectionInfo.id

            drawObject = self.getDrawObject("COLLECTIONS")
            drawObject.setCollectionEnable(self.collectionInfo.id, makeVisible)
            drawObject.renderAllViews()

    def getDrawObject(self, name):
        parent = om.getOrCreateContainer('Collections')
        return parent.findChild(name)

    def addToView(self, view):
        if view in self.views:
            return
        self.views.append(view)
        view.renderer().AddActor(self.actor)
        view.render()

    def setEnabled(self, enabled):
        print enabled
        print "sfdasdf"


class CollectionsObject(om.ObjectModelItem):

    def __init__(self, name, actor):

        om.ObjectModelItem.__init__(self, name, om.Icons.Collections)


        self.actor = actor
        self.actor.SetUseBounds(False)
        self.addProperty('Visible', actor.GetVisibility())
        self.addProperty('Alpha', 0.8, attributes=om.PropertyAttributes(decimals=2, minimum=0, maximum=1.0, singleStep=0.1, hidden=False))
        self.addProperty('Color Mode', 2, attributes=om.PropertyAttributes(enumNames=['Flat', 'Print', 'Height', 'Gray', 'Semantic']))
        self.addProperty('Occ. Space', 1, attributes=om.PropertyAttributes(enumNames=['Hide', 'Show']))
        self.addProperty('Free Space', 0, attributes=om.PropertyAttributes(enumNames=['Hide', 'Show']))
        self.addProperty('Structure', 0, attributes=om.PropertyAttributes(enumNames=['Hide', 'Show']))
        self.addProperty('Tree Depth', 16, attributes=om.PropertyAttributes(decimals=0, minimum=1, maximum=16, singleStep=1.0))
        self.views = []

    def _onPropertyChanged(self, propertySet, propertyName):
        om.ObjectModelItem._onPropertyChanged(self, propertySet, propertyName)

        if propertyName == 'Visible':
            self.actor.SetVisibility(self.getProperty(propertyName))
            self.renderAllViews()

        elif propertyName == 'Alpha':
            self.actor.setAlphaOccupied(self.getProperty(propertyName))
            self.renderAllViews()

        elif propertyName == 'Occ. Space':
            self.actor.enableOcTreeCells(self.getProperty(propertyName))
            self.renderAllViews()

        elif propertyName == 'Free Space':
            self.actor.enableFreespace(self.getProperty(propertyName))
            self.renderAllViews()

        elif propertyName == 'Structure':
            self.actor.enableOctreeStructure(self.getProperty(propertyName))
            self.renderAllViews()

        elif propertyName == 'Tree Depth':
            self.actor.changeTreeDepth(self.getProperty(propertyName))
            self.renderAllViews()

        elif propertyName == 'Color Mode':
            heightColorMode = self.getProperty(propertyName)
            self.actor.setColorMode(heightColorMode)
            self.renderAllViews()

    def addToView(self, view):
        if view in self.views:
            return
        self.views.append(view)
        view.renderer().AddActor(self.actor)
        view.render()

    def renderAllViews(self):
        for view in self.views:
            view.render()

    def onRemoveFromObjectModel(self):
        self.removeFromAllViews()

    def removeFromAllViews(self):
        for view in list(self.views):
            self.removeFromView(view)
        assert len(self.views) == 0

    def removeFromView(self, view):
        assert view in self.views
        self.views.remove(view)
        view.renderer().RemoveActor(self.actor)
        view.render()

    def getCollectionsInfo(self):
        numberOfCollections = self.actor.getCollectionsSize()
        print "numberOfCollections: ", numberOfCollections

        self.collectionInfos = []
        for i in range(0,numberOfCollections):
            cId = self.actor.getCollectionsId(i)
            cName = self.actor.getCollectionsName(i)
            cType = self.actor.getCollectionsType(i)
            cShow = self.actor.getCollectionsShow(i)
            cInfo = CollectionInfo(cId, cName, cType, cShow )
            self.collectionInfos.append(cInfo)
            print i, cId

    def disableOne(self):
        self.setCollectionEnable(1,False)

    def setCollectionEnable(self, cId, enable):
        self.actor.setEnabled(cId, enable)

    def on_obj_collection_data(self, msgBytes):
        self.actor.on_obj_collection_data(msgBytes.data())
        self.getCollectionsInfo()
        self.renderAllViews()

    def on_link_collection_data(self, msgBytes):
        self.actor.on_link_collection_data(msgBytes.data())
        self.getCollectionsInfo()
        self.renderAllViews()

    def on_points_collection_data(self, msgBytes):
        self.actor.on_points_collection_data(msgBytes.data())
        self.getCollectionsInfo()
        self.renderAllViews()

managerInstance = None

class CollectionsManager(object):

    def __init__(self, view):
        assert LCMGL_AVAILABLE
        self.view = view
        self.subscriber = None
        self.enable()

    def isEnabled(self):
        return self.subscriber is not None

    def setEnabled(self, enabled):
        if enabled and not self.subscriber:
            #self.subscriber = lcmUtils.addSubscriber('LCMGL.*', callback=self.onMessage)
            self.subscriber = lcmUtils.addSubscriber('OBJECT_COLLECTION', callback=self.on_obj_collection_data)
            self.subscriber1 = lcmUtils.addSubscriber('LINK_COLLECTION', callback=self.on_link_collection_data)
            self.subscriber2 = lcmUtils.addSubscriber('POINTS_COLLECTION', callback=self.on_points_collection_data)
        elif not enabled and self.subscriber:
            lcmUtils.removeSubscriber(self.subscriber)
            self.subscriber = None

    def enable(self):
        self.setEnabled(True)

    def disable(self):
        self.setEnabled(False)

    def on_obj_collection_data(self, msgBytes, channel):
        msg = lcmCollections.object_collection_t.decode(msgBytes.data())
        drawObject = self.getDrawObject("COLLECTIONS")
        if not drawObject:
            drawObject = self.addDrawObject("COLLECTIONS", msgBytes)
        drawObject.on_obj_collection_data(msgBytes)

    def on_link_collection_data(self, msgBytes, channel):
        msg = lcmCollections.link_collection_t.decode(msgBytes.data())
        drawObject = self.getDrawObject("COLLECTIONS")
        if not drawObject:
            drawObject = self.addDrawObject("COLLECTIONS", msgBytes)
        drawObject.on_link_collection_data(msgBytes)

    def on_points_collection_data(self, msgBytes, channel):
        msg = lcmCollections.point3d_list_collection_t.decode(msgBytes.data())
        drawObject = self.getDrawObject("COLLECTIONS")
        if not drawObject:
            drawObject = self.addDrawObject("COLLECTIONS", msgBytes)
        drawObject.on_points_collection_data(msgBytes)

        self.addAllObjects()

    def getDrawObject(self, name):
        parent = om.getOrCreateContainer('Collections')
        return parent.findChild(name)

    def addDrawObject(self, name, msgBytes):
        actor = vtk.vtkCollections()
        obj = CollectionsObject(name, actor)
        om.addToObjectModel(obj, om.getOrCreateContainer('Collections'))
        obj.addToView(self.view)
        return obj

    def addAllObjects(self):
        drawObject = self.getDrawObject("COLLECTIONS")
        if not drawObject:
            return

        for coll in drawObject.collectionInfos:
            actor = vtk.vtkCollections()
            obj = CollectionInfoObject(coll, actor)
            om.addToObjectModel(obj, om.getOrCreateContainer('COLLECTIONS'))
            obj.addToView(self.view)


    def getDrawObject2(self, name):
        parent = om.getOrCreateContainer('COLLECTIONS')
        return parent.findChild(name)

    def addDrawObject2(self, name, msgBytes):
        actor = vtk.vtkCollections()
        obj = CollectionsObject(name, actor)
        om.addToObjectModel(obj, om.getOrCreateContainer('COLLECTIONS'))
        obj.addToView(self.view)
        return obj


def init(view):
    if not hasattr(vtk, 'vtkCollections'):
        return None

    global managerInstance
    managerInstance = CollectionsManager(view)

    return managerInstance
