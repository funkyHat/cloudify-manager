#########
# Copyright (c) 2013 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  * See the License for the specific language governing permissions and
#  * limitations under the License.

import json
import uuid

import jsonpickle
from deployment_update.constants import (ENTITY_TYPES,
                                         ACTION_TYPES)

from manager_exceptions import UnknownModificationStageError


class SerializableObject(object):

    def __getstate__(self):
        return {field: getattr(self, field) for field in self.fields}

    def to_dict(self):
        return json.loads(jsonpickle.encode(self, unpicklable=False))

    def to_json(self):
        return jsonpickle.encode(self, unpicklable=False)


class BlueprintState(SerializableObject):
    fields = {
        'id', 'plan', 'description', 'created_at', 'updated_at',
        'main_file_name'
    }

    def __init__(self, **kwargs):
        self.plan = kwargs['plan']
        self.id = kwargs['id']
        self.description = kwargs['description']
        self.created_at = kwargs['created_at']
        self.updated_at = kwargs['updated_at']
        self.main_file_name = kwargs['main_file_name']


class Snapshot(SerializableObject):
    CREATED = 'created'
    FAILED = 'failed'
    CREATING = 'creating'
    UPLOADED = 'uploaded'

    END_STATES = [CREATED, FAILED, UPLOADED]

    fields = {'id', 'created_at', 'status', 'error'}

    def __init__(self, **kwargs):
        self.id = kwargs['id']
        self.created_at = kwargs['created_at']
        self.status = kwargs['status']
        self.error = kwargs['error']


class Deployment(SerializableObject):
    fields = {'id', 'description', 'created_at', 'updated_at', 'blueprint_id',
              'workflows', 'permalink', 'inputs', 'policy_types',
              'policy_triggers', 'groups', 'outputs', 'description',
              'scaling_groups'}

    def __init__(self, **kwargs):
        self.id = kwargs['id']
        self.created_at = kwargs['created_at']
        self.updated_at = kwargs['updated_at']
        self.blueprint_id = kwargs['blueprint_id']
        self.workflows = kwargs['workflows']
        self.inputs = kwargs['inputs']
        self.policy_types = kwargs['policy_types']
        self.policy_triggers = kwargs['policy_triggers']
        self.groups = kwargs['groups']
        self.scaling_groups = kwargs['scaling_groups']
        self.description = kwargs['description']
        self.outputs = kwargs['outputs']
        self.permalink = None  # TODO: implement


class DeploymentUpdateStep(SerializableObject):

    fields = {'id', 'action', 'entity_type', 'entity_id'}

    def __init__(self, action, entity_type, entity_id, id=str(uuid.uuid4())):

        if entity_type not in ENTITY_TYPES:
            raise UnknownModificationStageError(
                'illegal modification entity type')

        if action not in ACTION_TYPES:
            raise UnknownModificationStageError(
                'illegal modification operation')

        self.action = action
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.id = id


class DeploymentUpdate(SerializableObject):

    fields = {'id', 'deployment_id', 'steps', 'state', 'deployment_plan',
              'deployment_update_nodes', 'deployment_update_node_instances',
              'deployment_update_deployment', 'modified_entity_ids',
              'execution_id', 'created_at'}

    def __init__(self,
                 deployment_id,
                 deployment_plan,
                 state='staged',
                 id=None,
                 steps=(),
                 deployment_update_nodes=None,
                 deployment_update_node_instances=None,
                 deployment_update_deployment=None,
                 modified_entity_ids=None,
                 execution_id=None,
                 created_at=None):
        self.id = id or '{0}-{1}'.format(deployment_id, uuid.uuid4())
        self.deployment_id = deployment_id
        self.deployment_plan = deployment_plan
        self.state = state
        self.steps = [DeploymentUpdateStep(**step) for step in (steps or [])]
        self.deployment_update_nodes = deployment_update_nodes
        self.deployment_update_node_instances = \
            deployment_update_node_instances
        self.deployment_update_deployment = deployment_update_deployment
        self.modified_entity_ids = modified_entity_ids
        self.execution_id = execution_id
        self.created_at = created_at


class DeploymentModification(SerializableObject):
    STARTED = 'started'
    FINISHED = 'finished'
    ROLLEDBACK = 'rolledback'

    END_STATES = [FINISHED, ROLLEDBACK]

    fields = {'id', 'deployment_id', 'modified_nodes', 'node_instances',
              'status', 'created_at', 'ended_at', 'context'}

    def __init__(self, **kwargs):
        self.id = kwargs['id']
        self.created_at = kwargs['created_at']
        self.ended_at = kwargs['ended_at']
        self.status = kwargs['status']
        self.deployment_id = kwargs['deployment_id']
        self.modified_nodes = kwargs['modified_nodes']
        self.node_instances = kwargs['node_instances']
        self.context = kwargs['context']


class Execution(SerializableObject):
    TERMINATED = 'terminated'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    PENDING = 'pending'
    STARTED = 'started'
    CANCELLING = 'cancelling'
    FORCE_CANCELLING = 'force_cancelling'

    STATES = [TERMINATED, FAILED, CANCELLED, PENDING, STARTED,
              CANCELLING, FORCE_CANCELLING]
    END_STATES = [TERMINATED, FAILED, CANCELLED]
    ACTIVE_STATES = [state for state in STATES if state not in END_STATES]

    fields = {'id', 'status', 'deployment_id', 'workflow_id', 'blueprint_id',
              'created_at', 'error', 'parameters', 'is_system_workflow'}

    def __init__(self, **kwargs):
        self.id = kwargs['id']
        self.status = kwargs['status']
        self.deployment_id = kwargs['deployment_id']
        self.workflow_id = kwargs['workflow_id']
        self.blueprint_id = kwargs['blueprint_id']
        self.created_at = kwargs['created_at']
        self.error = kwargs['error']
        self.parameters = kwargs['parameters']
        self.is_system_workflow = kwargs['is_system_workflow']


class DeploymentNode(SerializableObject):
    """
    Represents a node in a deployment.
    """

    fields = {
        'id', 'deployment_id', 'blueprint_id', 'type', 'type_hierarchy',
        'number_of_instances', 'planned_number_of_instances',
        'deploy_number_of_instances', 'host_id', 'properties',
        'operations', 'plugins', 'relationships', 'plugins_to_install',
        'min_number_of_instances', 'max_number_of_instances'
    }

    def __init__(self, **kwargs):
        self.id = kwargs['id']
        self.deployment_id = kwargs['deployment_id']
        self.blueprint_id = kwargs['blueprint_id']
        self.type = kwargs['type']
        self.type_hierarchy = kwargs['type_hierarchy']
        self.number_of_instances = kwargs['number_of_instances']
        self.planned_number_of_instances = kwargs[
            'planned_number_of_instances']
        self.deploy_number_of_instances = kwargs['deploy_number_of_instances']
        self.min_number_of_instances = kwargs['min_number_of_instances']
        self.max_number_of_instances = kwargs['max_number_of_instances']
        self.host_id = kwargs['host_id']
        self.properties = kwargs['properties']
        self.operations = kwargs['operations']
        self.plugins = kwargs['plugins']
        self.relationships = kwargs['relationships']
        self.plugins_to_install = kwargs['plugins_to_install']


class DeploymentNodeInstance(SerializableObject):
    """
    Represents a node instance in a deployment.
    """
    fields = {
        'id', 'deployment_id', 'runtime_properties', 'state', 'version',
        'relationships', 'node_id', 'host_id', 'scaling_groups'
    }

    def __init__(self, **kwargs):
        self.id = kwargs['id']
        self.node_id = kwargs['node_id']
        self.deployment_id = kwargs['deployment_id']
        self.runtime_properties = kwargs['runtime_properties']
        self.state = kwargs['state']
        self.version = kwargs['version']
        self.relationships = kwargs['relationships']
        self.host_id = kwargs['host_id']
        self.scaling_groups = kwargs['scaling_groups']


class ProviderContext(SerializableObject):
    fields = {'context', 'name'}

    def __init__(self, **kwargs):
        self.context = kwargs['context']
        self.name = kwargs['name']


class Plugin(SerializableObject):
    """
    Represents a wheel plugin
    """
    fields = {'id', 'package_name', 'archive_name', 'package_source',
              'package_version', 'supported_platform', 'distribution',
              'distribution_version', 'distribution_release', 'wheels',
              'excluded_wheels', 'supported_py_versions', 'uploaded_at'}

    def __init__(self, **kwargs):
        self.id = kwargs['id']
        self.package_name = kwargs['package_name']
        self.archive_name = kwargs['archive_name']
        self.package_source = kwargs['package_source']
        self.package_version = kwargs['package_version']
        self.supported_platform = kwargs['supported_platform']
        self.distribution = kwargs['distribution']
        self.distribution_version = kwargs['distribution_version']
        self.distribution_release = kwargs['distribution_release']
        self.wheels = kwargs['wheels']
        self.excluded_wheels = kwargs['excluded_wheels']
        self.supported_py_versions = kwargs['supported_py_versions']
        self.uploaded_at = kwargs['uploaded_at']
