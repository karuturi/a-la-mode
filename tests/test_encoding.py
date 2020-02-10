from a_la_mode import Task, Dag, sha, dissoc
from bencode import bencode
from toolz.dicttoolz import dissoc
from deepdiff import DeepDiff
import pytest

eg_dag = Dag({
    'schedule': '@daily'
})

eg_dag.task('download_images',
            {
                'image': 'collage',
                'sha': '1qe34',
                'command': "python dl_images.py"
            })

eg_dag.task('blur',
            {
                'image': 'collage',
                'sha': '6f09d',
                'command': "python transform_images.py blur"
            })

eg_dag.task('edge_enhance',
            {
                'image': 'collage',
                'sha': '1qe34',
                'command': "python transform_images.py edge_enhance"

            })

eg_dag.task('collage',
            {
                'image': 'collage',
                'sha': '1qe34',
                'command': "python collage.py"
            })

for task in [eg_dag.blur, eg_dag.edge_enhance]:
    task.add_dep(eg_dag.download_images)

for task in [eg_dag.blur, eg_dag.edge_enhance]:
    eg_dag.collage.add_dep(task)

encoded_dag = eg_dag.encode()
eg_dag.blur.spec['sha'] = 'qwetr3'

changed_dag = eg_dag
encoded_changed_dag = changed_dag.encode()

def test_unchanged():
    assert encoded_dag['meta'] == encoded_changed_dag['meta']
    for task in ['download_images', 'edge_enhance']:
        assert encoded_dag['tasks'][task] == encoded_changed_dag['tasks'][task]

def test_changed():
    assert DeepDiff(encoded_dag, encoded_changed_dag)['values_changed'].keys() == \
           set(["root['tasks']['blur']['output']",
                "root['tasks']['blur']['sha']",
                "root['tasks']['collage']['output']",
                "root['tasks']['collage']['inputs']['blur']"])

def test_values_match():
    assert encoded_changed_dag['tasks']['blur']['output'] == encoded_changed_dag['tasks']['collage']['inputs']['blur']
    assert encoded_changed_dag['tasks']['blur']['sha'] ==  'qwetr3'

def test_outputs():
    for _name, task in encoded_dag['tasks'].items():
        output = task['output']
        assert output == sha(bencode(dissoc(task, 'output')))

def test_inputs():
    for task in eg_dag.tasks:
        assert {dep.name for dep in task.deps} == \
               set(encoded_dag['tasks'][task.name]['inputs'].keys())

def test_incorrect_task_name():
    with pytest.raises(AttributeError) as e_info:
        eg_dag.not_there