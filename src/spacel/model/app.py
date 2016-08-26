import logging

logger = logging.getLogger('spacel')


class SpaceApp(object):
    def __init__(self, orbit, params={}):
        self.name = params.get('name', 'test')
        self.orbit = orbit
        regions = params.get('regions')
        if regions:
            self.regions = [region for region in regions
                            if region in orbit.regions]
        else:
            self.regions = orbit.regions
        self.hostnames = params.get('hostnames', ())
        self.instance_type = params.get('instance_type', 't2.nano')
        self.instance_min = params.get('instance_min', 1)
        self.instance_max = params.get('instance_max', 2)
        self.scheme = params.get('scheme', 'internet-facing')
        self.health_check = params.get('health_check', 'TCP:80')
        self.local_health_check = params.get('health_check', 'TCP:80')

        public_ports = params.get('public_ports', {80: {}})
        self.public_ports = {port: SpaceServicePort(port_params)
                             for port, port_params in public_ports.items()}

        self.private_ports = params.get('private_ports', {})
        self.volumes = params.get('volumes', {})

        self.services = {}
        services = params.get('services', {})
        for service_name, service_params in services.items():
            service_env = service_params.get('environment', {})
            unit_file = service_params.get('unit_file')
            if unit_file:
                non_docker = SpaceService(service_name, unit_file, service_env)
                self.services[service_name] = non_docker
                continue

            docker_image = service_params.get('image')
            if docker_image:
                ports = service_params.get('ports', {})
                volumes = service_params.get('volumes', {})
                docker = SpaceDockerService(service_name, docker_image, ports,
                                            volumes, service_env)
                self.services[service_name] = docker
                continue

            logger.warn('Invalid service: %s', service_name)
        self.alarms = params.get('alarms', {})

    @property
    def full_name(self):
        return '%s-%s' % (self.orbit.name, self.name)


class SpaceServicePort(object):
    def __init__(self, params={}):
        self.scheme = params.get('scheme', 'HTTP')
        default_scheme = self.scheme == 'HTTPS' and 'HTTP' or self.scheme
        self.internal_scheme = params.get('internal_scheme', default_scheme)

        self.sources = params.get('sources', ('0.0.0.0/0',))
        # TODO: HTTPS parameters: cert, ciphers


class SpaceService(object):
    def __init__(self, name, unit_file, environment={}):
        self.name = name
        self.unit_file = unit_file
        self.environment = environment


class SpaceDockerService(SpaceService):
    def __init__(self, name, image, ports={}, volumes={}, environment={}):
        docker_run_flags = ''
        docker_run_flags += SpaceDockerService._dict_flags('p', ports)
        docker_run_flags += SpaceDockerService._dict_flags('v', volumes)

        if environment:
            docker_run_flags += ' --env-file /files/%s.env' % name

        service_name = '%s.service' % name
        unit_file = """[Unit]
Description={0}
Requires=spacel-agent.service

[Service]
User=space
TimeoutStartSec=0
Restart=always
StartLimitInterval=0
ExecStartPre=-/usr/bin/docker pull {1}
ExecStartPre=-/usr/bin/docker kill %n
ExecStartPre=-/usr/bin/docker rm %n
ExecStart=/usr/bin/docker run --rm --name %n{2} {1}
ExecStop=/usr/bin/docker stop %n
""".format(name, image, docker_run_flags)
        super(SpaceDockerService, self).__init__(service_name, unit_file,
                                                 environment)

    @staticmethod
    def _dict_flags(flag, items):
        if not items:
            return ''
        pad_flag = ' -%s ' % flag
        return pad_flag + pad_flag.join(['%s:%s' % (k, v)
                                         for k, v in items.items()])
