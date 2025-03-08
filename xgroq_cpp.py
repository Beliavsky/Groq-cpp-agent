import groq
import subprocess
import re
import shutil
import time
from datetime import datetime
import os
import platform

"""
This script uses the Groq API to generate a C++ program based on a prompt, iteratively
refines it until it compiles successfully with a specified compiler, and optionally runs
the resulting executable. Configuration parameters are read from 'config.txt', including
the model, max attempts, max time for code generation, prompt file, source file, whether
to run the executable, whether to print the final code, whether to print compiler error
messages, the compiler, and compiler options. The Groq API key is read from 'groq_key.txt'.
Generated code includes comments with the prompt file name, model, generation time, and
timestamp. Previous attempts are archived with numbered suffixes (e.g., foo1.cpp, foo2.cpp).
Lines starting with a backtick (`) are commented out as they are invalid in C++.

Config file format (config.txt):
    model: <model_name> (e.g., llama-3.3-70b-versatile)
    max_attempts: <integer> (e.g., 5)
    max_time: <seconds> (e.g., 10)
    prompt_file: <filename> (e.g., prompt.txt)
    source_file: <filename> (e.g., foo.cpp)
    run_executable: <yes/no> (e.g., yes)
    print_code: <yes/no> (e.g., yes)
    print_compiler_error_messages: <yes/no> (e.g., yes)
    compiler: <compiler_name> (e.g., g++)
    compiler_options: <options> (e.g., -O2 -Wall) [optional, can be empty]

Dependencies: groq, subprocess, re, shutil, time, datetime, os, platform
Requires: Specified compiler installed (e.g., g++)
"""

# Read Groq API key from file
with open("groq_key.txt", "r") as key_file:
    api_key = key_file.read().strip()

# Read configuration parameters from file
config_file = "config.txt"
config = {}
with open(config_file, "r") as f:
    for line in f:
        if not line.strip():
            continue  # skip blank lines
        key, value = line.strip().split(": ", 1)  # Split on first ": " only
        config[key] = value

# Extract parameters
model = config["model"]
max_attempts = int(config["max_attempts"])
max_time = float(config["max_time"])  # Maximum cumulative generation time in seconds
prompt_file = config["prompt_file"]
source_file = config["source_file"]
base_name = os.path.splitext(source_file)[0]  # Extract base name (e.g., "foo" from "foo.cpp")
run_executable = config["run_executable"].lower() == "yes"
print_code = config["print_code"].lower() == "yes"
print_compiler_error_messages = config["print_compiler_error_messages"].lower() == "yes"
compiler = config["compiler"]
compiler_options = config.get("compiler_options", "").split()  # Handle empty compiler options

# Determine executable extension based on platform
is_windows = platform.system() == "Windows"
executable_ext = ".exe" if is_windows else ""
executable_path = f".{os.sep}{base_name}{executable_ext}"  # e.g., ".\foo.exe" on Windows, "./foo" on Unix

# Initialize Groq client
client = groq.Groq(api_key=api_key)

def generate_code(prompt):
    # Measure time taken to generate code
    start_time = time.time()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000
    )
    end_time = time.time()
    generation_time = end_time - start_time

    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Extract raw content
    content = response.choices[0].message.content

    # Split content into lines
    lines = content.splitlines()

    # Find the index of the first ```cpp line
    code_start_idx = -1
    for i, line in enumerate(lines):
        if line.strip() == "```cpp":
            code_start_idx = i
            break

    # Comment out everything up to and including ```cpp
    if code_start_idx != -1:
        for i in range(code_start_idx + 1):
            if not lines[i].startswith("//"):
                lines[i] = "//" + lines[i]
        # Extract code after ```cpp until ``` (if present)
        code_lines = []
        for line in lines[code_start_idx + 1:]:
            if line.strip() == "```":
                break
            code_lines.append(line)
        code = "\n".join(code_lines)
    else:
        # If no ```cpp found, comment everything and use it as-is
        code = "\n".join("//" + line if not line.startswith("//") else line for line in lines)

    # Comment out lines starting with a backtick within the code
    code_lines = code.splitlines()
    for i in range(len(code_lines)):
        if code_lines[i].strip().startswith("`"):
            code_lines[i] = "//" + code_lines[i]
    code = "\n".join(code_lines)

    # Calculate lines of code (excluding header)
    loc = len([line for line in code.splitlines() if line.strip()])

    # Add comment lines to the top of the code
    header = (
        f"// Generated from prompt file: {prompt_file}\n"
        f"// Model used: {model}\n"
        f"// Time generated: {timestamp}\n"
        f"// Generation time: {generation_time:.3f} seconds\n"
    )
    return header + code, generation_time, loc

def test_code(code, filename=source_file, attempt=1):
    # If not the first attempt, save a copy with suffix (e.g., foo1.cpp, foo2.cpp)
    if attempt > 1:
        archive_filename = f"{base_name}{attempt-1}.cpp"
        shutil.copyfile(filename, archive_filename)
    
    # Write the new code to the source file
    with open(filename, "w") as f:
        f.write(code)
    
    # Compile with specified compiler and options
    compile_command = [compiler] + compiler_options + ["-o", base_name, filename]
    if print_compiler_error_messages:
        result = subprocess.run(
            compile_command,
            capture_output=True,
            text=True
        )
        error = result.stderr
    else:
        with open("temp_compiler_error.txt", "w") as error_file:
            result = subprocess.run(
                compile_command,
                stderr=error_file,
                text=True
            )
        with open("temp_compiler_error.txt", "r") as error_file:
            error = error_file.read()
        os.remove("temp_compiler_error.txt")
    
    return result.returncode == 0, error

# Read initial prompt from file specified in config
with open(prompt_file, "r") as f:
    prompt = f.read() + "Only output C++ code. Do not give commentary.\n"
    print("prompt:\n" + prompt)
print("model: " + model + "\n")
code, initial_gen_time, initial_loc = generate_code(prompt)
total_gen_time = initial_gen_time
attempts = 1

# Iterate until compilation succeeds or limits are exceeded
while True:
    success, error = test_code(code, attempt=attempts)
    if success:
        print(f"Code compiled successfully after {attempts} {'attempt' if attempts == 1 else 'attempts'} (generation time: {initial_gen_time if attempts == 1 else gen_time:.3f} seconds, LOC={initial_loc if attempts == 1 else loc})!")
        if print_code:
            print("Final version:\n\n", code)
        if run_executable:
            if os.path.exists(executable_path):
                print(f"Running executable: {executable_path}")
                run_result = subprocess.run(executable_path, capture_output=True, text=True, input="5\n")
                if run_result.returncode == 0:
                    print("\nOutput:\n", run_result.stdout)
                else:
                    print(f"\nExecution failed with error: {run_result.stderr}")
            else:
                print(f"\nExecutable not found at {executable_path}. Ensure compilation succeeded.")
        else:
            print("\nSkipping execution as per config (run_executable: no)")
        print(f"\nTotal generation time: {total_gen_time:.3f} seconds across {attempts} {'attempt' if attempts == 1 else 'attempts'}")
        break
    else:
        if print_compiler_error_messages:
            print(f"Attempt {attempts} failed with error (generation time: {initial_gen_time if attempts == 1 else gen_time:.3f} seconds, LOC={initial_loc if attempts == 1 else loc}): {error}")
        else:
            print(f"Attempt {attempts} failed (error details suppressed, generation time: {initial_gen_time if attempts == 1 else gen_time:.3f} seconds, LOC={initial_loc if attempts == 1 else loc})")
        
        # Check if we've exceeded max_time before generating more code
        if total_gen_time >= max_time:
            print(f"Max generation time ({max_time} seconds) exceeded after {attempts} attempts.")
            if print_code:
                print("Last code:\n", code)
            print(f"\nTotal generation time: {total_gen_time:.3f} seconds")
            break
        
        prompt = (
            f"The following C++ code failed to compile: \n```cpp\n{code}\n```\n"
            f"Error: {error}\nPlease fix the code and return it in a ```cpp``` block."
        )
        code, gen_time, loc = generate_code(prompt)
        total_gen_time += gen_time
        attempts += 1
        
        if attempts > max_attempts:
            print(f"Max attempts ({max_attempts}) reached.")
            if print_code:
                print("Last code:\n", code)
            print(f"Total generation time: {total_gen_time:.3f} seconds")
            break

# Print the compilation command
compile_command = [compiler] + compiler_options + ["-o", base_name, source_file]
print(f"\nCompilation command: {' '.join(compile_command)}")
