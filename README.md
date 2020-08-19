# JMH Params Data Generator
This is a simple Python 3 script used to generate datasets of JMH executions with varied parameter values.

## Usage
The script generates data by executing selected benchmarks over and over again, with randomly generated JMH parameter values. The script uses two configurations: projects and benchmarks to use are specified through a JSON config file; execution parameters are specified as commandline parameters.

### JSON file
The script assumes that you have locally checked out the JMH project(s) you want to benchmark. Further, a configuration file in JSON format is needed (refer to the included examples). For each metric parameter (e.g., an int, double, or float) you need to specify minimum and maximum values. For categorical parameters (e.g., strings), a complete list of all values needs to be provided.

Benchmark names do not have to be exact matches -- the script supports JMH's pattern matching syntax, so you can (in principle) configure the system so that multiple (or even all) benchmarks are matched through a single entry in the config file. However, due to technical limitations of the JMH commandline interface, you need to pass the same parameter values to all benchmarks that you match in this manner.

### Commandline parameters
The script supports the following commandline parameters:
- --projects (path to the JSON config to use, mandatory)
- --outfile (path to the CSV file that the data will be written to, mandatory
- -i (how often shall the script repeat benchmarking before finishing, mandatory)
- -c (how many parameter combinations shall the script use in each run? the script allows you to test multiple parameter values in a single execution, mandatory)
- -rc (how many values to generate for range parameters - you will likely don't have to change this value, but it should be smaller than the range of all parameters)
- --tmp_file (where should JMH log intermediary results? the default is tmp.json)
- --jmh_std (where should the JMH output get piped to? this is useful for debugging, the default is out.log)
- --jmh_cmd (what string template to use to launch JMH processes? the syntax for this parameter is difficult to explain, it's better to look directly at the code -- function run_benchmark -- to see how it is being used and then configure for your system if necessary)

### Anything else?
The script is essentially a small wrapper around running JMH via bash. Most things that can go wrong are related to launching the JMH process. If you are running into problems, make sure that simply executing the benchmarks themselves directly (e.g., via java -jar benchmarks.jar) works. This also means that the benchmarks have to be pre-compiled and need to be available in a JAR file. The script currently does not support launching the benchmarks via Maven or Gradle.