from modeling import *
from tqdm import tqdm
import subprocess, shlex
logger = logging.getLogger(__name__)


def get_frame_path(v, frame=0):
    base = os.path.abspath(os.path.join(settings.BASE_DIR, 'static', 'frames', v.slug))
    return v.getframepath(frame=frame, base=base)


def create_command_pwc(v):
    n = v.totalframes
    cmds = []
    for i in range(0, n-1):
        cmd = "python3 run.py --model default --first {} --second {} --out {}.flo"\
            .format(get_frame_path(v, i), get_frame_path(v, i+1), get_frame_path(v, i))
        cmds.append(cmd)
    return cmds


def write_command_pwc(v, output_file):
    cmds = create_command_pwc(v)
    with open(output_file, "w") as f:
        f.write("#!/bin/sh\n\n")
        for cmd in cmds:
            f.write(cmd + '\n')
    f.close()


def create_command_for_jobgroup(id):
    jobs = Job.objects.filter(group_id=id, completed=True).all()
    cmds = []
    for job in tqdm(jobs):
        segment = job.segment
        v = segment.video
        for i in range(segment.start, segment.stop-1):
            cmd = "python3 run.py --model default --first {} --second {} --out {}.flo" \
                .format(get_frame_path(v, i), get_frame_path(v, i + 1), get_frame_path(v, i))
            cmds.append(cmd)
    return cmds


def write_command_for_jobgroup(id, output_file):
    cmds = create_command_for_jobgroup(id)
    with open(output_file, "w") as f:
        f.write("#!/bin/sh\n\n")
        for cmd in cmds:
            f.write("echo '{}'\n".format(cmd))
            f.write(cmd + '\n')
    f.close()


if __name__ == '__main__':
    output_file = '{}/thirdparty/pytorch-pwc/{}.sh'
    write_command_for_jobgroup(id=2, output_file=output_file)
    # videos = Video.objects.all()
    # for v in tqdm(videos):
    #     write_command_pwc(v, output_file=output_file.format(settings.BASE_DIR, v.slug))