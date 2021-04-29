import json
import os
import argparse
import re
from typing import Tuple


def check_completeness_single_job(out_file: str,
                                  job_no: int,
                                  iteration: int) -> bool:
    """
    Check whether an individual inference job has been completed.

    Args:
        out_file: n5 file to save inference to.
        job_no: Number/id of the individual inference job.
        iteration: Iteration of the inference.

    Returns:
        If True, inference job has been completed.
    """
    if os.path.exists(os.path.join(out_file, 'list_gpu_{0:}.json'.format(job_no))) and os.path.exists(
            os.path.join(out_file, 'list_gpu_{0:}_{1:}_processed.txt'.format(job_no, iteration))):
        block_list = os.path.join(out_file, 'list_gpu_{0:}.json'.format(job_no))
        block_list_processed = os.path.join(out_file, 'list_gpu_{0:}_{1:}_processed.txt'.format(job_no, iteration))
        with open(block_list, 'r') as f:
            block_list = json.load(f)
            block_list = {tuple(coo) for coo in block_list}
        with open(block_list_processed, 'r') as f:
            list_as_str = f.read()
        list_as_str_curated = '[' + list_as_str[:list_as_str.rfind(']') + 1] + ']'
        processed_list = json.loads(list_as_str_curated)
        processed_list = {tuple(coo) for coo in processed_list}
        if processed_list < block_list:
            complete = False
        else:
            complete = True
    else:
        complete = False
    return complete


def check_completeness(out_file: str,
                       iteration: int) -> bool:
    """
    Check whether an inference has been completed.

    Args:
        out_file: n5 file to save inference to.
        iteration: Iteration of the inference.

    Returns:
        If True, inference has been completed.
    """
    completeness = []
    p = re.compile("list_gpu_(\d+).json")
    jobs = []
    if not os.path.exists(out_file):
        print(0)
        return 0
    for f in os.listdir(out_file):
        mo = p.match(f)
        if mo is not None:
            jobs.append(mo.group(1))
    if len(jobs) < 1:
       print(0)
       return False
    for i in jobs:
        completeness.append(check_completeness_single_job(out_file, i, iteration))
    print(int(all(completeness)))
    return all(completeness)


def get_output_paths(raw_data_path: str,
                     setup_path: str,
                     output_path: str,
                     iteration: int) -> Tuple[str, str]:
    """
    Get output directory and file, can be autogenerated.

    Args:
        raw_data_path: path to the raw data
        setup_path: Path containing setup.
        output_path: N5 container to save output to, autogenerated if None.
        iteration: Iteration to pull inference for.
    Returns:
        Tuple of output directory and output "file" (n5-container).
    """
    if output_path is None:
        basename, n5_filename = os.path.split(raw_data_path)
        assert n5_filename.endswith('.n5')

        # output directory, e.g. "(...)/setup01/HeLa_Cell2_4x4x4nm/"
        all_data_dir, cell_identifier = os.path.split(basename)
        output_dir = os.path.join(setup_path, cell_identifier)

        # output file, e.g. "(...)/setup01/HeLa_Cell2_4x4x4nm/HeLa_Cell2_4x4x4nm_it10000.n5"
        base_n5_filename, n5 = os.path.splitext(n5_filename)
        output_filename = base_n5_filename + '_it{0:}'.format(iteration) + n5
        out_file = os.path.join(output_dir, output_filename)
    else:
        assert output_path.endswith('.n5') or output_path.endswith('.n5/')
        output_dir = os.path.abspath(os.path.dirname(output_path))
        out_file = os.path.abspath(output_path)
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    if not os.path.exists(out_file):
        os.mkdir(out_file)
    return output_dir, out_file


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("n_job", type=int, help="Number of jobs inference was split over.")
    parser.add_argument("n_cpus", type=int, help="Number of cpus to use per job.")
    parser.add_argument("raw_data_path", type=str, help="Path to n5 container that contains raw data.")
    parser.add_argument("iteration", type=int, help="Iteration to pull inference for.")
    parser.add_argument("--raw_ds", type=str, default="volumes/raw/s0",
                        help="Dataset in n5 container (`raw_data_path`) for raw data.")
    parser.add_argument("--mask_ds", type=str, default="volumes/masks/foreground",
                        help="Dataset in n5 container (`raw_data_path`) for mask data. Can be None if no mask exists.")
    parser.add_argument("--setup_path", type=str, default='.', help="Path containing setup.")
    parser.add_argument("--output_path", type=str, default=None, help="N5 container to save output to.")
    parser.add_argument("--finish_interrupted", type=bool, default=False,
                        help="Whether running this is to finsih an interrupted inference job.")
    parser.add_argument("--factor", type=int, default=None, help="Factor to normalize raw data by.")
    parser.add_argument("--min_sc", type=float, default=None, help="Minimum intensity (mapped to -1)")
    parser.add_argument("--max_sc", type=float, default=None, help="Maximum intensity (mapped to 1)")
    parser.add_argument("--float_range", type=int, nargs="+", default=(-1, 1))
    parser.add_argument("--safe_scale", type=bool, default=False)
    parser.add_argument("--resolution", type=int, nargs="+", default=None)
    args = parser.parse_args()
    raw_data_path = args.raw_data_path
    iteration = args.iteration
    setup_path = args.setup_path
    output_path = args.output_path
    _, out_file = get_output_paths(raw_data_path, setup_path, output_path)
    check_completeness(out_file, iteration)


if __name__ == "__main__":
    main()
