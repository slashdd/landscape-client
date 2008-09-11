from landscape.tests.helpers import LandscapeTest

from landscape.manager.store import ManagerStore


class ManagerStoreTest(LandscapeTest):

    def setUp(self):
        super(ManagerStoreTest, self).setUp()
        self.filename = self.makeFile()
        self.store = ManagerStore(self.filename)
        self.store.add_graph(1, u"file 1", u"user1")

    def test_get_unknow_graph(self):
        graph = self.store.get_graph(1000)
        self.assertIdentical(graph, None)

    def test_get_graph(self):
        graph = self.store.get_graph(1)
        self.assertEquals(graph, (1, u"file 1", u"user1"))

    def test_get_graphs(self):
        graphes = self.store.get_graphes()
        self.assertEquals(graphes, [(1, u"file 1", u"user1")])

    def test_get_no_graphes(self):
        self.store.remove_graph(1)
        graphes = self.store.get_graphes()
        self.assertEquals(graphes, [])

    def test_add_graph(self):
        self.store.add_graph(2, u"file 2", u"user2")
        graph = self.store.get_graph(2)
        self.assertEquals(graph, (2, u"file 2", u"user2"))

    def test_add_update_graph(self):
        self.store.add_graph(1, u"file 2", u"user2")
        graph = self.store.get_graph(1)
        self.assertEquals(graph, (1, u"file 2", u"user2"))

    def test_remove_graph(self):
        self.store.remove_graph(1)
        graphes = self.store.get_graphes()
        self.assertEquals(graphes, [])

    def test_remove_unknow_graph(self):
        self.store.remove_graph(2)
        graphes = self.store.get_graphes()
        self.assertEquals(graphes, [(1, u"file 1", u"user1")])
