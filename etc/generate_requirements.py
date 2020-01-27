import re

requirements_re = re.compile("install_requires=\[\s((^.+'(.+)',.+$)+)\s+\],\n\s+e", re.DOTALL+re.MULTILINE)

package_re = re.compile('(?P<package>.+?)(?P<specifier>[~<>=]{1,2})(?P<version>[\d\w.+_]+)(;(?P<restriction>.+)|$)?')

setup_requirements = list()
requirements_txt = list()

requirements_dict = {}


def add_to_dict(package):
    if package['package'] not in requirements_dict:
        requirements_dict[package['package']] = package
    else:
        if package['version'] != requirements_dict[package['package']]['version']:
            raise AttributeError("Can't resolve mismatched versions")
        if package['restriction'] and not requirements_dict[package['package']]['restriction']:
            requirements_dict[package['package']]['restriction'] = package['restriction']
        if package['specifier'] !=  requirements_dict[package['package']]['specifier']:
            if requirements_dict[package['package']]['specifier'] == "~=" and package['specifier'] == "==":
                requirements_dict[package['package']]['specifier'] = "=="


with open('../libweasyl/setup.py') as setupy_file:
    setuppy = setupy_file.read()
    for line in requirements_re.search(setuppy).group(1).split('\n'):
        line = line.split(',')[0].replace("'", '').strip()
        add_to_dict(package_re.search(line).groupdict())




with open('../etc/requirements.txt') as requirements_file:
    for line in requirements_file:
        line = line.split('#')[0].strip()
        line = line.split(',')[0].replace("'", '').strip()
        try:
            add_to_dict(package_re.search(line).groupdict())
        except AttributeError:
            pass

with open('_requirements.txt', 'w') as out:
    for k, v in requirements_dict.items():
        out.write("{}{}{}{}\n".format(k, v['specifier'], v['version'], ";"+v['restriction'] if v['restriction'] else ''))
# print(requirements_dict)

#
#     print(set(requirements))
#     out.write("\n".join(list(set(requirements))))