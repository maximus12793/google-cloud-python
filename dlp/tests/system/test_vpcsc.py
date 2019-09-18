# -*- coding: utf-8 -*-
#
# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# flake8: noqa

# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
import os

from gcp_devrel.testing import eventually_consistent
from gcp_devrel.testing.flaky import flaky
import google.api_core.exceptions
import google.cloud.datastore
import google.cloud.exceptions
import google.cloud.pubsub
import google.cloud.storage

import pytest
import inspect_content

GCLOUD_PROJECT = os.environ.get("GCLOUD_PROJECT", None)
TEST_BUCKET_NAME = os.environ.get("TEST_BUCKET_NAME", None)

RESOURCE_DIRECTORY = os.path.join(os.path.dirname(__file__), "resources")
RESOURCE_FILE_NAMES = ["test.txt"]

TOPIC_ID = "dlp-test"
SUBSCRIPTION_ID = "dlp-test-subscription"
DATASTORE_KIND = "DLP test kind"

@pytest.fixture(scope="module")
def bucket():
    # Creates a GCS bucket, uploads files required for the test, and tears down
    # the entire bucket afterwards.

    client = google.cloud.storage.Client()
    try:
        bucket = client.get_bucket(TEST_BUCKET_NAME)
    except google.cloud.exceptions.NotFound:
        bucket = client.create_bucket(TEST_BUCKET_NAME)

    # Upoad the blobs and keep track of them in a list.
    blobs = []
    for name in RESOURCE_FILE_NAMES:
        path = os.path.join(RESOURCE_DIRECTORY, name)
        blob = bucket.blob(name)
        blob.upload_from_filename(path)
        blobs.append(blob)

    # Yield the object to the test; lines after this execute as a teardown.
    yield bucket

    # Delete the files.
    for blob in blobs:
        blob.delete()

    # Attempt to delete the bucket; this will only work if it is empty.
    bucket.delete()


@pytest.fixture(scope="module")
def topic_id():
    # Creates a pubsub topic, and tears it down.
    publisher = google.cloud.pubsub.PublisherClient()
    topic_path = publisher.topic_path(GCLOUD_PROJECT, TOPIC_ID)
    try:
        publisher.create_topic(topic_path)
    except google.api_core.exceptions.AlreadyExists:
        pass

    yield TOPIC_ID

    publisher.delete_topic(topic_path)


@pytest.fixture(scope="module")
def subscription_id(topic_id):
    # Subscribes to a topic.
    subscriber = google.cloud.pubsub.SubscriberClient()
    topic_path = subscriber.topic_path(GCLOUD_PROJECT, topic_id)
    subscription_path = subscriber.subscription_path(GCLOUD_PROJECT, SUBSCRIPTION_ID)
    try:
        subscriber.create_subscription(subscription_path, topic_path)
    except google.api_core.exceptions.AlreadyExists:
        pass

    yield SUBSCRIPTION_ID

    subscriber.delete_subscription(subscription_path)


@pytest.fixture(scope="module")
def datastore_project():
    # Adds test Datastore data, yields the project ID and then tears down.
    datastore_client = google.cloud.datastore.Client()

    kind = DATASTORE_KIND
    name = "DLP test object"
    key = datastore_client.key(kind, name)
    item = google.cloud.datastore.Entity(key=key)
    item["payload"] = "My name is Gary Smith and my email is gary@example.com"

    datastore_client.put(item)

    yield GCLOUD_PROJECT

    datastore_client.delete(key)


@flaky
@pytest.mark.skipif(
    GCLOUD_PROJECT is None,
    reason="Missing environment variable: GCLOUD_PROJECT",
)
def test_inspect_datastore(
        datastore_project, topic_id, subscription_id, capsys):
    @eventually_consistent.call
    def _():
        inspect_content.inspect_datastore(
            GCLOUD_PROJECT,
            datastore_project,
            DATASTORE_KIND,
            topic_id,
            subscription_id,
            ['FIRST_NAME', 'EMAIL_ADDRESS', 'PHONE_NUMBER'])

        out, _ = capsys.readouterr()
        assert 'Info type: EMAIL_ADDRESS' in out


@flaky
@pytest.mark.skipif(
    GCLOUD_PROJECT is None,
    reason="Missing environment variable: GCLOUD_PROJECT",
)
def test_inspect_gcs_file(bucket, topic_id, subscription_id, capsys):
    inspect_content.inspect_gcs_file(
        GCLOUD_PROJECT,
        bucket.name,
        "test.txt",
        topic_id,
        subscription_id,
        ["FIRST_NAME", "EMAIL_ADDRESS", "PHONE_NUMBER"],
        timeout=420,
    )

    out, _ = capsys.readouterr()
    assert "Info type: EMAIL_ADDRESS" in out

# TODO: Enable BigQuery scanning

"""
