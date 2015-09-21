#########
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
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
#
from flask import request
from flask_restful_swagger import swagger

from manager_rest import resources
from manager_rest.resources import (marshal_with,
                                    exceptions_handled,
                                    verify_json_content_type,
                                    verify_parameter_in_request_body)
from manager_rest.resources import verify_and_convert_bool
from manager_rest import models
from manager_rest import responses_v2
from manager_rest import manager_exceptions
from manager_rest.storage_manager import get_storage_manager
from manager_rest.blueprints_manager import get_blueprints_manager
from manager_rest.blueprints_manager import \
    TRANSIENT_WORKERS_MODE_ENABLED_DEFAULT


def verify_and_create_filters(fields):
    """
    Decorator for extracting filter parameters from the request arguments and
    verifying their validity according to the provided fields.
    :param fields: a set of valid filter fields.
    :return: a Decorator for creating and validating the accepted fields.
    """
    def verify_and_create_filters_dec(f):
        def verify_and_create(*args, **kw):
            filters = {k: v for k, v in request.args.iteritems()
                       if not k.startswith('_')}
            unknowns = [k for k in filters.iterkeys() if k not in fields]
            if unknowns:
                raise manager_exceptions.BadParametersError(
                    'Filter keys \'{key_names}\' do not exist. Allowed '
                    'filters are: {fields}'
                    .format(key_names=unknowns, fields=list(fields)))
            return f(filters=filters, *args, **kw)
        return verify_and_create
    return verify_and_create_filters_dec


def _create_filter_params_list_description(parameters, list_type):
    return [{'name': filter_val,
             'description': 'List {type} matching the \'{filter}\' '
                            'filter value'.format(type=list_type,
                                                  filter=filter_val),
             'required': False,
             'allowMultiple': False,
             'dataType': 'string',
             'defaultValue': None,
             'paramType': 'query'} for filter_val in parameters]


class Blueprints(resources.Blueprints):

    @swagger.operation(
        responseClass='List[{0}]'.format(responses_v2.BlueprintState.__name__),
        nickname="list",
        notes='Returns a list of submitted blueprints for the optionally '
              'provided filter parameters {0}'
        .format(models.BlueprintState.fields),
        parameters=_create_filter_params_list_description(
            models.BlueprintState.fields,
            'blueprints'
        )
    )
    @exceptions_handled
    @marshal_with(responses_v2.BlueprintState)
    @verify_and_create_filters(models.BlueprintState.fields)
    def get(self, _include=None, filters=None, **kwargs):
        """
        List uploaded blueprints
        """
        return get_blueprints_manager().blueprints_list(
            include=_include, filters=filters)


class BlueprintsId(resources.BlueprintsId):

    @swagger.operation(
        responseClass=responses_v2.BlueprintState,
        nickname="getById",
        notes="Returns a blueprint by its id."
    )
    @exceptions_handled
    @marshal_with(responses_v2.BlueprintState)
    def get(self, blueprint_id, _include=None, **kwargs):
        """
        Get blueprint by id
        """
        with resources.skip_nested_marshalling():
            return super(BlueprintsId, self).get(blueprint_id=blueprint_id,
                                                 _include=_include,
                                                 **kwargs)

    @swagger.operation(
        responseClass=responses_v2.BlueprintState,
        nickname="upload",
        notes="Submitted blueprint should be an archive "
              "containing the directory which contains the blueprint. "
              "Archive format may be zip, tar, tar.gz or tar.bz2."
              " Blueprint archive may be submitted via either URL or by "
              "direct upload.",
        parameters=[{'name': 'application_file_name',
                     'description': 'File name of yaml '
                                    'containing the "main" blueprint.',
                     'required': False,
                     'allowMultiple': False,
                     'dataType': 'string',
                     'paramType': 'query',
                     'defaultValue': 'blueprint.yaml'},
                    {'name': 'blueprint_archive_url',
                     'description': 'url of a blueprint archive file',
                     'required': False,
                     'allowMultiple': False,
                     'dataType': 'string',
                     'paramType': 'query'},
                    {
                        'name': 'body',
                        'description': 'Binary form of the tar '
                                       'gzipped blueprint directory',
                        'required': True,
                        'allowMultiple': False,
                        'dataType': 'binary',
                        'paramType': 'body'}],
        consumes=[
            "application/octet-stream"
        ]

    )
    @exceptions_handled
    @marshal_with(responses_v2.BlueprintState)
    def put(self, blueprint_id, **kwargs):
        """
        Upload a blueprint (id specified)
        """
        with resources.skip_nested_marshalling():
            return super(BlueprintsId, self).put(blueprint_id=blueprint_id,
                                                 **kwargs)

    @swagger.operation(
        responseClass=responses_v2.BlueprintState,
        nickname="deleteById",
        notes="deletes a blueprint by its id."
    )
    @exceptions_handled
    @marshal_with(responses_v2.BlueprintState)
    def delete(self, blueprint_id, **kwargs):
        """
        Delete blueprint by id
        """
        with resources.skip_nested_marshalling():
            return super(BlueprintsId, self).delete(
                blueprint_id=blueprint_id, **kwargs)


class Executions(resources.Executions):

    @swagger.operation(
        responseClass='List[{0}]'.format(responses_v2.Execution.__name__),
        nickname="list",
        notes='Returns a list of executions for the optionally provided filter'
              ' parameters: {0}'.format(models.Execution.fields),
        parameters=_create_filter_params_list_description(
            models.Execution.fields, 'executions') + [
            {'name': '_include_system_workflows',
             'description': 'Include executions of system workflows',
             'required': False,
             'allowMultiple': True,
             'dataType': 'bool',
             'defaultValue': False,
             'paramType': 'query'}
        ]
    )
    @exceptions_handled
    @marshal_with(responses_v2.Execution)
    @verify_and_create_filters(models.Execution.fields)
    def get(self, _include=None, filters=None, **kwargs):
        """
        List executions
        """
        deployment_id = request.args.get('deployment_id')
        if deployment_id:
            get_blueprints_manager().get_deployment(deployment_id,
                                                    include=['id'])
        is_include_system_workflows = verify_and_convert_bool(
            '_include_system_workflows',
            request.args.get('_include_system_workflows', 'false'))

        executions = get_blueprints_manager().executions_list(
            filters=filters,
            is_include_system_workflows=is_include_system_workflows,
            include=_include)
        return executions


class Deployments(resources.Deployments):

    @swagger.operation(
        responseClass='List[{0}]'.format(responses_v2.Deployment.__name__),
        nickname="list",
        notes='Returns a list existing deployments for the optionally provided'
              ' filter parameters: {0}'.format(models.Deployment.fields),
        parameters=_create_filter_params_list_description(
            models.Deployment.fields,
            'deployments'
        )
    )
    @exceptions_handled
    @marshal_with(responses_v2.Deployment)
    @verify_and_create_filters(models.Deployment.fields)
    def get(self, _include=None, filters=None, **kwargs):
        """
        List deployments
        """
        deployments = get_blueprints_manager().deployments_list(
            include=_include, filters=filters)
        return deployments


class DeploymentModifications(resources.DeploymentModifications):
    @swagger.operation(
        responseClass='List[{0}]'.format(
            responses_v2.DeploymentModification.__name__),
        nickname="listDeploymentModifications",
        notes='Returns a list of deployment modifications for the optionally '
              'provided filter parameters: {0}'
        .format(models.DeploymentModification.fields),
        parameters=_create_filter_params_list_description(
            models.DeploymentModification.fields,
            'deployment modifications'
        )
    )
    @exceptions_handled
    @marshal_with(responses_v2.DeploymentModification)
    @verify_and_create_filters(models.DeploymentModification.fields)
    def get(self, _include=None, filters=None, **kwargs):
        """
        List deployment modifications
        """
        modifications = get_storage_manager().deployment_modifications_list(
            include=_include, filters=filters)
        return modifications


class Nodes(resources.Nodes):

    @swagger.operation(
        responseClass='List[{0}]'.format(responses_v2.Node.__name__),
        nickname="listNodes",
        notes='Returns a nodes list for the optionally provided filter '
              'parameters: {0}'.format(models.DeploymentNode.fields),
        parameters=_create_filter_params_list_description(
            models.DeploymentNode.fields,
            'nodes'
        )
    )
    @exceptions_handled
    @marshal_with(responses_v2.Node)
    @verify_and_create_filters(models.DeploymentNode.fields)
    def get(self, _include=None, filters=None, **kwargs):
        """
        List nodes
        """
        nodes = get_storage_manager().get_nodes(include=_include,
                                                filters=filters)
        return nodes


class NodeInstances(resources.NodeInstances):

    @swagger.operation(
        responseClass='List[{0}]'.format(responses_v2.NodeInstance.__name__),
        nickname="listNodeInstances",
        notes='Returns a node instances list for the optionally provided '
              'filter parameters: {0}'
        .format(models.DeploymentNodeInstance.fields),
        parameters=_create_filter_params_list_description(
            models.DeploymentNodeInstance.fields,
            'node instances'
        )
    )
    @exceptions_handled
    @marshal_with(responses_v2.NodeInstance)
    @verify_and_create_filters(models.DeploymentNodeInstance.fields)
    def get(self, _include=None, filters=None, **kwargs):
        """
        List node instances
        """
        node_instances = get_storage_manager().get_node_instances(
            include=_include, filters=filters)
        return node_instances


class ProviderContext(resources.ProviderContext):
    @swagger.operation(
        responseClass=responses_v2.ProviderContext,
        notes="Updates the provider context",
        parameters=[{'name': 'global_parallel_executions_limit',
                     'description': "the global parallel executions limit",
                     'required': True,
                     'allowMultiple': False,
                     'dataType': 'int',
                     'paramType': 'body'},
                    ],
        consumes=[
            "application/json"
        ]
    )
    @exceptions_handled
    @marshal_with(responses_v2.ProviderContext)
    def patch(self, **kwargs):
        """
        modifies provider context configuration
        """
        verify_json_content_type()
        request_json = request.json
        verify_parameter_in_request_body('global_parallel_executions_limit',
                                         request_json)

        provider_ctx = get_storage_manager().get_provider_context()
        bootstrap_ctx = provider_ctx.context.get('cloudify', {})

        transient_dep_workers_mode_enabled = bootstrap_ctx.get(
            'transient_deployment_workers_mode', {}).get(
            'enabled', TRANSIENT_WORKERS_MODE_ENABLED_DEFAULT)
        if not transient_dep_workers_mode_enabled:
            raise manager_exceptions.BadParametersError(
                "can't modify global_parallel_executions_limit since transient"
                ' deployment workers mode is disabled')

        limit = request_json['global_parallel_executions_limit']
        if type(limit) is not int:
            raise manager_exceptions.BadParametersError(
                'global_parallel_executions_limit parameter should be of type'
                ' int, but is instead of type {0}'.format(
                    type(limit).__name__))

        trans_dep_workers_mode = bootstrap_ctx.get(
            'transient_deployment_workers_mode', {})
        trans_dep_workers_mode['global_parallel_executions_limit'] = limit

        bootstrap_ctx['transient_deployment_workers_mode'] = \
            trans_dep_workers_mode
        provider_ctx.context['cloudify'] = bootstrap_ctx
        get_storage_manager().update_provider_context(provider_ctx)
        return get_storage_manager().get_provider_context()