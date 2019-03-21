#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import random
import subprocess
from operators import *
from compute_minimal_mutants import *
from mutant_util import *



# Generates a report with option -g (general) and reads important information from the report
def readDataG(program):

    #filename
    fname = "/tmp/g-report"
    
    #pass the output of the report to the file
    statement = "report -g " + program + " >" + fname
    os.system(statement)
    
    #open the file
    report_file = open(fname, "r")
    
    #ignores empty line
    qtd = report_file.readline()
    
    #get the number of testcases used
    qtd = report_file.readline() # reads number test cases
    tcases = int(qtd)

    #ignores total mutants
    qtd = report_file.readline() 
    
    #reads the number of ACTIVE mutants (only those of a specific operator)
    qtd = report_file.readline() 
    mutants = int(qtd) 
    
    #read number equiv mutants
    qtd = report_file.readline() 
    equiv = int(qtd)

    #read MS
    qtd = report_file.readline() 
    ms = float(qtd)
    
    #read alive mutants
    qtd = report_file.readline() 
    alive = int(qtd)
    
    #read anomalous mutants
    qtd = report_file.readline() 
    anom = int(qtd)

    #build results list
    result = [0.0, 0, 0, 0]
    result[0] = ms
    result[1] = mutants - anom
    result[2] = equiv
    result[3] = tcases
    
    #results = [mutation_score, valid_mutants, equivalent_mutants, num_testcases]
    return result



# This function selects and executes a set of mutant operators
def execute_mutants_by_op(program, operator):

    print "I: Executing all mutants of the operator: {}".format(operator)

    #enable all test cases
    statement = "tcase -e " + program 
    os.system(statement)
    print statement

    #enable all mutants again for futher execution
    statement = 'exemuta -select -u- 1 ' + program
    os.system(statement)
    print statement

    #select the mutants of the operator
    operator = opToString(operator) #this will handle "random %" operators
    print "I'm using: ", operator 

    #some cases such as "random %" operators, string statmant need to be a little bit diferent
    if "-" in operator:
        statement = "exemuta -select -all 0 " + operator + program
    
    #normal case
    else:
        statement = "exemuta -select -all 0 -" + operator + " 1 " + program
    
    os.system(statement)
    print statement

    #execute all testcases against the subset of mutants generated by operator
    statement = "exemuta -exec " + program
    os.system(statement)
    print statement

    print "I: Will gather the results to the operator: {}".format(operator)  

    #will compute the results for this execution
    results = readDataG(program) 

    return results




"""
This function should compute and select the effective test cases, i.e., those that kill at least one mutant. 
"""
def goodTestcases(program, seed):

    print "I: Will select the effective test cases, i.e., those that killed at least one mutant."

    #uses a random order to select the test cases because of seed (check proteum manpages)
    statement = 'list-good -i -research -seed ' + str(seed) + ' ' + program + " 2>/dev/null | wc -l"
    
    #run the operation in background and save the results in a file
    temp_file = os.popen2(statement)
    print statement

    #get the number of userful testcases
    ntcase = int(temp_file[1].readline()) # reads the number of userful test cases
    
    #close the file
    temp_file[1].close()

    print "I: Number of good testcases: {}".format(str(ntcase))

    return ntcase



"""
Compute minimal mutants, execute and compute results about this execution
"""
def execute_minimal_mutants(program):

    print "I: Will execute the minimal set of mutants"

    #enable all mutants again for futher execution
    statement = 'exemuta -select -u- 1 ' + program
    os.system(statement)
    print statement

    #Computing the Minimal Mutans (Return a list with the ID of the mutants)
    minimal_mutants = compute_minimal_set(program)

    #log about minimal
    print "Program: " + program
    print "Number of minimals: " , len(minimal_mutants)
    print "Minimal mutants: ",  minimal_mutants   

    #Convert the list in a suitable string to execute in proteum module
    string_mutant = mutant_string(minimal_mutants)

    #This comand will produce a output with all information about every one minimal mutant
    #with that is possible extract the mutation operator used to create each mutant 
    statement = 'muta -l -x \"' + string_mutant + '\" ' + program

    #Save the output of the execution in a string
    #The comand is not realy executed, just processed. Then the output is saved in 'shell_output'
    shell_output = str(subprocess.check_output(statement, shell=True))
    print statement

    #Execute the get_all_mutants.
    #This returns a dictionary with the following structure:
    # MutantOperator ---> Mutants genereted by this operator
    mutants_by_operator, mutants_status  = get_all_mutants(shell_output)  #At this point this dictionary have just information about minimal mutants

    print "Minimal mutants by operator:"
    print mutants_by_operator

    #select only mutants from minimal set
    statement = 'exemuta -select -x \"' + string_mutant + '\" ' + program
    os.system(statement)
    print statement

    #executes the testcases against minimum set
    os.system('exemuta -exec ' + program)
    print statement 
    
    print "I: Will gather the results related to the minimal set of mutants "

    #compute results
    results = readDataG(program)

    return results



#This function will compute the data related to a given mutant operator
def getOpProgDataV4(program, seed, operator):
        
    # Note: these 3 next functins MUST be called in sequence

    #select a set of mutants, execute them and retrive the a valid information about the execution
    results_by_op = execute_mutants_by_op(program, operator) 
    
    #return the number of effective test cases
    number_good_testcases = goodTestcases(program, seed) 

    #execute minimal mutants with the good test set
    results_by_minimal = execute_minimal_mutants(program)  

    
    #results information -> [mutation_score, valid_mutants, equivalent_mutants, num_testcases]

    #store results
    result = [0.0, 0, 0, 0]

    result[0] = results_by_minimal[0] #get the mutation score from the minimal execution with a given testset suitable to an operator 
    result[1] = results_by_op[1]      #number of valid mutants of an operator given operator
    result[2] = results_by_op[2]      #number of equivalent mutants of that operator
    result[3] = number_good_testcases #number of testcases used to kill all the mutants of a given operator

    #The data is returned in a sequnce of 
    #[0] - mutation score in relation to the complete set
    #[1] - number of mutants for the op set
    #[2] - number of equiv mutants for the op set
    #[3] - number of test cases required

    return result  
