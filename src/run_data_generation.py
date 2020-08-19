import argparse
import json
import os
from random import sample
from random import randint
from random import uniform
from datetime import datetime

# commandline argument parsing
def parse_cmd_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--projects', dest='projects',
                        required=True, help='JSON project config file to use')
    parser.add_argument('--outfile', dest='out',
                        required=True, help='CSV file to write the benchmark data to')
    parser.add_argument('-i', dest='iterations',
                        required=True, type=int, help='How many iterations to run')
    parser.add_argument('-c', dest='combinations',
                    required=True, type=int, help='How many parameter combinations to use in each iteration')
    parser.add_argument('-rc', dest='range_combinations',
                    default="100",
                    help='How many values to generate for range parameters (should be >> -c)')
    parser.add_argument('--tmp_file', dest='tmpfile',
                default="tmp.json",
                help='JMH JSON file to log results to')
    parser.add_argument('--jmh_std', dest='cmd_output',
            default="out.log",
            help='File to pipe JMH output to')
    # parser.add_argument('--jmh_cmd', dest='jmh',
    #                     default="java -jar %s %s %s -i 10 -wi 10 -f 1 -r 1 -w 1 -rf json -rff %s",
    #                     help='Shell command to start a benchmark run')
    parser.add_argument('--jmh_cmd', dest='jmh',
                        default="java -jar %s %s %s -i 10 -wi 10 -f 1 -r 1 -w 1 -rf json -rff %s",
                        help='Shell command to start a benchmark run')
    return parser.parse_args()

# parse the JSON file with configurations of projects and benchmarks to use
def parse_project_json(file):
    with open(file) as f:
        return json.load(f)

# scaffolding to execute benchmarks for a project
def execute_project(project, args):
    params = generate_parameter_list(project, args)
    run_project(project, params, args)

# generate a list of concrete parameter values to use in an interation
# (per benchmark and parameter)
def generate_parameter_list(project, args):
    param_list = {}
    for benchmark in project['benchmarks']:
        param_list[benchmark['name']] = generate_parameter_list_for_benchmark(benchmark, args)
    return param_list

# generate the parameter list for one concrete benchmark
def generate_parameter_list_for_benchmark(benchmark, args):
    p = {}
    for param in benchmark['parameters']:
        if param['type'] == 'category':
            p[param['name']] = sample(param['values'], args.combinations)
        elif param['type'] == 'range':
            min, max = param['min_val'], param['max_val']
            p[param['name']] = [str(randint(min, max)) for _ in range(args.combinations)]
        elif param['type'] == 'float_range':
            min, max = param['min_val'], param['max_val']
            p[param['name']] = [str(uniform(min, max)) for _ in range(args.combinations)]
    return p

# start a single JMH run for every individual benchmark
# (this is necessary due to technical limitations of configuring JMH over the commandline)
def run_project(project, params, args):
    for b in project['benchmarks']:
        run_benchmark(project, b, params, args)

# use the shell to start a single JMH run
def run_benchmark(project, benchmark, params, args):
    param_list = generate_arg_list(params[benchmark['name']])
    jmh_file = project['path']+"/"+project['jmh_file']
    cmd = args.jmh % (jmh_file, benchmark['name'], param_list, args.tmpfile)
    appending_cmd = cmd + " >> %s 2>&1" % args.cmd_output
    print("Running command: \"%s\"" % appending_cmd)
    os.system(appending_cmd)
    results = parse_result_file(project['name'], args.tmpfile)
    append_to_outfile(results, args.out)

# convert the generated benchmark parameter list into the format expected by JMH
def generate_arg_list(params):
    str = " "
    for p in params.keys():
        str += "-p %s=%s " % (p, ','.join(params[p]))
    return str

# this method parses the JSON format the JMH produces
def parse_result_file(project, file):
    with open(file) as f:
        json_results = json.load(f)
        results = []
        for b in json_results:
            encoded_params = encode_params(b['params'])
            for fork in b['primaryMetric']['rawData']:
                for result in fork:
                    results.append((project, b['benchmark'], encoded_params, str(result)))
        return results

# encode parameters into a single string so that we can save them easily to CSV
def encode_params(params):
    str = ""
    for param in params.keys():
        str += "%s=%s+" % (param, params[param])
    str = str.rstrip('+')
    return str

# append results to an (at this point existing) output CSV file
def append_to_outfile(results, file):
    if not(os.path.exists(file)):
        create_outfile(file)
    with open(file, "a") as f:
        for result in results:
            f.write(';'.join(result)+'\n')

# create a new outfile (incl. header)
def create_outfile(file):
    with open(file, "w") as f:
        f.write('Project;Benchmark;Params;Measurement\n')

# estimate how much time we have left in this run
def project_remaining_time(time, done, total):
    frac = float(done) / total
    remaining = ((time * total) / done) - time
    return (round(remaining, 2), 100 * round(frac, 2))

# start main method
args = parse_cmd_args()
project_config = parse_project_json(args.projects)
projects = project_config['projects']

# results = parse_result_file('EclipseCollections', args.tmpfile)
# append_to_outfile(results, args.out)

total_time = 0
for i in range(0, args.iterations):
    begin = datetime.now()
    print("Starting iteration %i of %i" % (i+1, args.iterations))
    for p in projects:
        print(" Executing project %s" % p['name'])
        execute_project(p, args)
    end = datetime.now()
    time = ((end - begin).total_seconds() / 3600)
    total_time += time
    remaining, percent = project_remaining_time(total_time, i+1, args.iterations)
    print(" Executing took %f hours. Total %f hours, %f to go (%f percent)." %
        (round(time, 2), round(total_time, 2), remaining, percent))

print("Finished. Output written to %s" % args.out)
