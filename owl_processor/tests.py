import json
from django.http import response
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import exceptions, status
from .models import Onto
from pandas.core.common import flatten


class TestSetUp(APITestCase):
    def setUp(self):
        self.user_data = {
            "email": "email@gmail.com",
            "password": "username1234",
        }

        self.sample_owlsource = {
            "formURL": "https://raw.githubusercontent.com/CommonCoreOntology/CommonCoreOntologies/master/cco-merged/MergedAllCoreOntology-v1.3-2021-03-01.ttl",
            "formName": "test",
        }
        return super().setUp()

    def tearDown(self):
        return super().tearDown()


class TestViews(TestSetUp):
    def authenticate(self):
        self.client.post(reverse("register"), self.user_data)
        response = self.client.post(
            reverse("login"),
            {"username": "email@gmail.com", "password": "username1234"},
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {response.data['token']}"
        )
        self.user_id = response.data['user_id']

    def test_owltable(self):
        response = self.client.post(
            reverse("onto_owltable"), self.sample_owlsource)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "test")
        self.assertEqual(
            response.data["onto_source"],
            self.sample_owlsource["formURL"],
        )
        self.assertEqual(response.data["author"], "no user")

    def test_ontolist_should_not_post_with_no_auth(self):

        response = self.client.post(
            reverse("onto_lists"), self.sample_owlsource)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_ontolist_should_post_with_auth(self):
        previous_onto_count = Onto.objects.all().count()
        self.authenticate()

        response = self.client.post(
            reverse("onto_lists"), self.sample_owlsource)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Onto.objects.all().count(), previous_onto_count + 1)
        self.assertEqual(response.data["title"], "test")
        self.assertEqual(
            response.data["onto_source"],
            self.sample_owlsource["formURL"],
        )
        self.assertEqual(response.data["author"], self.user_id)

    def test_ontolist_should_not_exceed_limits(self):
        self.authenticate()
        for i in range(10):
            test_owlresource = {
                "formURL": "http://www.daml.org/2003/01/periodictable/PeriodicTable.owl",
                "formName": f"test{i}",
            }
            response = self.client.post(
                reverse("onto_lists"), test_owlresource)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        test_owlresource_extra = {
            "formURL": "http://www.daml.org/2003/01/periodictable/PeriodicTable.owl",
            "formName": "extra"}

        response = self.client.post(
            reverse("onto_lists"), test_owlresource_extra)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_ontochange_shoud_not_change_with_no_auth(self):
        sample_updateowlsource = {
            "formURL": "http://www.daml.org/2003/01/periodictable/PeriodicTable.owl",
            "formName": "test",
        }
        response = self.client.put(
            reverse("onto_change", args=(1,)), sample_updateowlsource
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_ontochange_shoud_with_auth(self):
        self.authenticate()
        # create first
        create_response = self.client.post(
            reverse("onto_lists"), self.sample_owlsource)

        # check update function

        sample_updateowlsource = {
            "formURL": "http://www.daml.org/2003/01/periodictable/PeriodicTable.owl",
            "formName": "testchanged",
        }
        update_response = self.client.put(
            reverse("onto_change", args=(create_response.data["id"],)),
            sample_updateowlsource,
        )

        changed_data = Onto.objects.filter(author=self.user_id).get(
            id=create_response.data["id"]
        )

        # check the data in databank of update function

        self.assertEqual(
            changed_data.onto_source,
            "http://www.daml.org/2003/01/periodictable/PeriodicTable.owl",
        )
        self.assertEqual(changed_data.title, "testchanged")

        # check the response data of update function

        self.assertEqual(
            update_response.data["onto_source"],
            "http://www.daml.org/2003/01/periodictable/PeriodicTable.owl",
        )
        self.assertEqual(update_response.data["title"], "testchanged")
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)

        # check delete function
        delete_response = self.client.delete(
            reverse("onto_change", args=(create_response.data["id"],))
        )

        # check the data in databank of delete function

        with self.assertRaises(Onto.DoesNotExist):
            Onto.objects.filter(author=self.user_id).get(
                id=create_response.data["id"]
            ),

        # check the response data of delete function

        self.assertEqual(delete_response.status_code,
                         status.HTTP_204_NO_CONTENT)


# class TestOnotable(APITestCase):
#     def test_owltable_funs(self):
#         sources = [{
#             "formURL": "https://protege.stanford.edu/ontologies/camera.owl",
#             "formName": "Cam",
#         }, {
#             "formURL": "https://protege.stanford.edu/ontologies/pizza/pizza.owl",
#             "formName": "Pizza",
#         }, {
#             "formURL": "http://owl.man.ac.uk/2006/07/sssw/people.owl",
#             "formName": "Peop",

#         }, {
#             "formURL": "https://raw.githubusercontent.com/Mat-O-Lab/MSEO/main/MSEO_mid.owl",
#             "formName": "test1",
#         }]
#         # counts: class, objectproperty, dataproperty, individual, annotation property, from protege
#         # camera,pizza, people, mid

#         # AP will have at least 8

#         counts = [[12, 7, 8, 2, 8],
#                   [99, 8, 0, 5, 8+8], [60, 14, 0, 22, 8], [1663, 286, 29, 515, 66]]
#         for i in range(len(sources)):
#             response = self.client.post(
#                 reverse("onto_owltable"), sources[i])
#             self.assertEqual(response.status_code, status.HTTP_200_OK)

#             table = json.loads(response.data["onto_table"]['table'])
#             tree = response.data["onto_table"]['tree']
#             df_length = []
#             # assert lens of df and in protege are equal
#             # assert tree and df have the same entities, no one is missing.
#             for j in ['Class', 'ObjectProperty', 'DatatypeProperty', 'Individual', 'AnnotationProperty']:
#                 entity = set(
#                     [x for x in table.keys() if table[x]['BelongsTo'] == j])
#                 df_length.append(len(entity))

#                 tree_entity = set(flatten(tree[j]))

#             self.assertEqual(df_length, counts[i])

#             self.assertEqual(tree_entity, entity)
