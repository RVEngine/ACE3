#!/usr/bin/env python3
"""
Author: SilentSpike
Crawl function headers to produce appropriate documentation of public functions.

Supported header sections:
 - Author(s) (with description below)
 - Arguments
 - Return Value
 - Example(s)
 - Public (by default function will only be documented if set to "Yes")

EXAMPLES
    document_functions common --debug
        Crawl only functions in addons/common and only reports debug messages.
"""

import os
import sys
import re
import argparse

class FunctionFile:
    def __init__(self, directory="."):
        self.directory = directory

        # False unless specified in processing
        self.debug = False

        # Empty until imported from file
        self.path = ""
        self.header = ""

        # Defaults until header is processed
        self.public = False
        self.authors = []
        self.description = ""
        self.arguments = []
        self.return_value = []
        self.example = ""

        # Filepath should only be logged once
        self.logged = False

    def import_header(self, file_path):
        self.path = file_path

        with open(file_path) as file:
            code = file.read()

        header_match = re.match(r"\s*/\*.+?\*/", code, re.S)
        if header_match:
            self.header = header_match.group(0)
        else:
            self.feedback("Missing header", 3)

    def has_header(self):
        return bool(self.header)

    def process_header(self, debug=False):
        # Detailed debugging occurs here so value is set
        self.debug = debug

        # Preemptively cut away the comment characters (and leading/trailing whitespace)
        self.header_text = "\n".join([x[3:].strip() for x in self.header.splitlines()])

        # Split the header into expected sections
        self.sections = re.split(r"^(Author|Argument|Return Value|Example|Public)s?:\s?", self.header_text, 0, re.M)

        # If public section is missing we can't continue
        public_raw = self.get_section("Public")
        if not public_raw:
            self.feedback("Public value undefined", 3)
            return

        # Determine whether the header is public
        self.public = self.process_public(public_raw)

        # Don't bother to process the rest if private
        # Unless in debug mode
        if not self.public and not self.debug:
            return

        # Retrieve the raw sections text for processing
        author_raw = self.get_section("Author")
        arguments_raw = self.get_section("Argument")
        return_value_raw = self.get_section("Return Value")
        example_raw = self.get_section("Example")

        # Author and description are stored in first section
        if author_raw:
            self.authors = self.process_author(author_raw)
            self.description = self.process_description(author_raw)

        if arguments_raw:
            self.arguments = self.process_arguments(arguments_raw)

        # Process return
        if return_value_raw:
            self.return_value = self.process_return_value(return_value_raw)

        # Process example
        if example_raw:
            self.example = example_raw.strip()

    def get_section(self, section_name):
        try:
            section_text = self.sections[self.sections.index(section_name) + 1]
            return section_text
        except ValueError:
            self.feedback("Missing \"{}\" header section".format(section_name), 2)
            return ""

    def process_public(self, raw):
        # Raw just includes an EOL character
        public_text = raw[:-1]

        if not re.match(r"(Yes|No)", public_text, re.I):
            self.feedback("Invalid public value \"{}\"".format(public_text), 2)

        return public_text.capitalize() == "Yes"

    def is_public(self):
        return self.public

    def process_author(self, raw):
        # Authors are listed on the first line
        authors_text = raw.splitlines()[0]

        # Seperate authors are divided by commas
        return authors_text.split(", ")

    def process_description(self, raw):
        # Just use all the lines after the authors line
        description_text = "".join(raw.splitlines(1)[1:])

        return description_text

    def process_arguments(self, raw):
        lines = raw.splitlines()

        if lines[0] == "None":
            return []

        if lines.count("") == len(lines):
            self.feedback("No arguments provided (use \"None\" where appropriate)", 2)
            return []

        if lines[-1] == "":
            lines.pop()
        else:
            self.feedback("No blank line after arguments list", 1)

        arguments = []
        for argument in lines:
            valid = re.match(r"^(\d+):\s(.+?)\<([\s\w]+?)\>(\s\(default: (.+)\))?$", argument)

            if valid:
                arg_index = valid.group(1)
                arg_name = valid.group(2)
                arg_types = valid.group(3)
                arg_default = valid.group(5)
                arg_notes = []

                if arg_index != str(len(arguments)):
                    self.feedback("Argument index {} does not match listed order".format(arg_index), 1)

                if arg_default == None:
                    arg_default = ""

                arguments.append([arg_index, arg_name, arg_types, arg_default, arg_notes])
            else:
                # Notes about the above argument won't start with an index
                # Only applies if there exists an above argument
                if re.match(r"^(\d+):", argument) or not arguments:
                    self.feedback("Malformed argument \"{}\"".format(argument), 2)
                else:
                    arguments[-1][-1].append(argument)

        return arguments

    def process_return_value(self, raw):
        return_value = raw.strip()

        if return_value.title() == "None":
            return ["None", "N/A"]

        valid = re.match(r"^(.+?)\<([\s\w]+?)\>", return_value)

        if valid:
            return_name = valid.group(1)
            return_types = valid.group(2)

        else:
            self.feedback("Malformed return value \"{}\"".format(return_value), 2)

        return [return_name, return_types]

    def log_file(self, error=False):
        # When in debug mode we only want to see the files with errors
        if not self.debug or error:
            if not self.logged:
                rel_path = os.path.relpath(self.path, self.directory)

                self.write("Processing... {}".format(rel_path), 1)
                self.logged = True

    def feedback(self, message, level=0):
        priority_str = ["Info","Warning","Error","Aborted"][level]

        self.log_file(level > 0)
        self.write("{0}: {1}".format(priority_str, message))

    def write(self, message, indent=2):
        to_print = ["  "]*indent
        to_print.append(message)
        print("".join(to_print))

def document_function(function):
    os.makedirs('../wiki/functions/', exist_ok=True)

    component = os.path.basename(os.path.dirname(os.path.dirname(function.path)))

    output = os.path.join('../wiki/functions/',component) + ".md"
    with open(output, "a+") as file:
        # Title
        file.write("\n## ace_{}_fnc_{}\n".format(component,os.path.basename(function.path)[4:-4]))
        # Description
        file.write("__Description__\n\n" + function.description)
        # Arguments
        file.write("__Parameters__\n\nIndex | Description | Datatype(s) | Default Value\n--- | --- | --- | ---\n")
        for argument in function.arguments:
            file.write("{} | {} | {} | {}\n".format(*argument))
        file.write("\n")
        # Return Value
        file.write("__Return Value__\n\nDescription | Datatype(s)\n--- | ---\n{} | {}\n\n".format(*function.return_value))
        # Example
        file.write("__Example__\n\n```\n{}\n```\n".format(function.example))
        # Authors
        file.write("\n__Authors__\n\n")
        for author in function.authors:
            file.write("- {}\n".format(author))
        # Horizontal rule
        file.write("\n---\n")

def crawl_dir(directory, debug=False):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".sqf") and file.startswith("fnc_"):
                file_path = os.path.join(root, file)

                # Attempt to import the header from file
                function = FunctionFile(directory)
                function.import_header(file_path)

                # Undergo data extraction and detailed debug
                if function.has_header():
                    function.process_header(debug)

                    # Placeholder
                    if function.is_public() and not debug:
                        document_function(function)
                        function.feedback("Publicly documented")

def main():
    print("""
    #########################
    # Documenting Functions #
    #########################
    """)

    parser = argparse.ArgumentParser()
    parser.add_argument('directory', nargs="?", type=str, default=".", help='only crawl specified module addon folder')
    parser.add_argument('--debug', action="store_true", help='only check for header debug messages')
    args = parser.parse_args()

    # abspath is just used for the terminal output
    prospective_dir = os.path.abspath(os.path.join('../../addons/',args.directory))
    if os.path.isdir(prospective_dir):
        print("Directory: {}".format(prospective_dir))
        crawl_dir(prospective_dir, args.debug)
    else:
        print("Invalid directory: {}".format(prospective_dir))

if __name__ == "__main__":
    main()