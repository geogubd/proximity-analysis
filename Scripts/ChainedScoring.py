# --------------------------------
# Name: ChainedScoring.py
# Purpose: This tool will add scoring fields for every field past based on a threshold, and two return values.
# Current Owner: David Wasserman
# Last Modified: 08/03/2017
# Copyright:   (c) CoAdapt
# ArcGIS Version:   10.4.1
# Python Version:   2.7
# --------------------------------
# Copyright 2016 David J. Wasserman
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# --------------------------------
# Import Modules
import os, sys, arcpy


# Function Definitions

def func_report(function=None, reportBool=False):
    """This decorator function is designed to be used as a wrapper with other functions to enable basic try and except
     reporting (if function fails it will report the name of the function that failed and its arguments. If a report
      boolean is true the function will report inputs and outputs of a function.-David Wasserman"""

    def func_report_decorator(function):
        def func_wrapper(*args, **kwargs):
            try:
                func_result = function(*args, **kwargs)
                if reportBool:
                    print("Function:{0}".format(str(function.__name__)))
                    print("     Input(s):{0}".format(str(args)))
                    print("     Ouput(s):{0}".format(str(func_result)))
                return func_result
            except Exception as e:
                print(
                    "{0} - function failed -|- Function arguments were:{1}.".format(str(function.__name__), str(args)))
                print(e.args[0])
        return func_wrapper
    if not function:  # User passed in a bool argument
        def waiting_for_function(function):
            return func_report_decorator(function)
        return waiting_for_function
    else:
        return func_report_decorator(function)


def arc_tool_report(function=None, arcToolMessageBool=False, arcProgressorBool=False):
    """This decorator function is designed to be used as a wrapper with other GIS functions to enable basic try and except
     reporting (if function fails it will report the name of the function that failed and its arguments. If a report
      boolean is true the function will report inputs and outputs of a function.-David Wasserman"""
    def arc_tool_report_decorator(function):
        def func_wrapper(*args, **kwargs):
            try:
                func_result = function(*args, **kwargs)
                if arcToolMessageBool:
                    arcpy.AddMessage("Function:{0}".format(str(function.__name__)))
                    arcpy.AddMessage("     Input(s):{0}".format(str(args)))
                    arcpy.AddMessage("     Ouput(s):{0}".format(str(func_result)))
                if arcProgressorBool:
                    arcpy.SetProgressorLabel("Function:{0}".format(str(function.__name__)))
                    arcpy.SetProgressorLabel("     Input(s):{0}".format(str(args)))
                    arcpy.SetProgressorLabel("     Ouput(s):{0}".format(str(func_result)))
                return func_result
            except Exception as e:
                arcpy.AddMessage(
                        "{0} - function failed -|- Function arguments were:{1}.".format(str(function.__name__),
                                                                                        str(args)))
                print(
                    "{0} - function failed -|- Function arguments were:{1}.".format(str(function.__name__), str(args)))
                print(e.args[0])
        return func_wrapper
    if not function:  # User passed in a bool argument
        def waiting_for_function(function):
            return arc_tool_report_decorator(function)
        return waiting_for_function
    else:
        return arc_tool_report_decorator(function)


@arc_tool_report
def arc_print(string, progressor_Bool=False):
    """ This function is used to simplify using arcpy reporting for tool creation,if progressor bool is true it will
    create a tool label."""
    casted_string = str(string)
    if progressor_Bool:
        arcpy.SetProgressorLabel(casted_string)
        arcpy.AddMessage(casted_string)
        print(casted_string)
    else:
        arcpy.AddMessage(casted_string)
        print(casted_string)


@arc_tool_report
def field_exist(featureclass, fieldname):
    """ArcFunction
     Check if a field in a feature class field exists and return true it does, false if not.- David Wasserman"""
    fieldList = arcpy.ListFields(featureclass, fieldname)
    fieldCount = len(fieldList)
    if (fieldCount >= 1)and fieldname.strip():  # If there is one or more of this field return true
        return True
    else:
        return False


@arc_tool_report
def add_new_field(in_table, field_name, field_type, field_precision="#", field_scale="#", field_length="#",
                  field_alias="#", field_is_nullable="#", field_is_required="#", field_domain="#"):
    """ArcFunction
    Add a new field if it currently does not exist. Add field alone is slower than checking first.- David Wasserman"""
    if field_exist(in_table, field_name):
        print(field_name + " Exists")
        arcpy.AddMessage(field_name + " Exists")
    else:
        print("Adding " + field_name)
        arcpy.AddMessage("Adding " + field_name)
        arcpy.AddField_management(in_table, field_name, field_type, field_precision, field_scale,
                                  field_length,
                                  field_alias,
                                  field_is_nullable, field_is_required, field_domain)
@arc_tool_report
def score_value(value,threshold_upper,threshold_lower=0,if_within_score=1,if_outside_score=0):
    """This function is intended to take a value (proximity for example), and check if it is <= a threshold,
    and return a score for if it is less than or more than based on the passed parameters. Defaults to binary (0,1)"""
    if value>=threshold_lower and value<=threshold_upper:
        return if_within_score
    else:
        return if_outside_score

# Main Function
def chained_scoring_func(in_fc, scoring_fields, threshold_upper,threshold_lower=0, if_less_score=1, if_more_score=0):
    """This tool will score fields based a  upper and lower bound threhsold, and return values to those fields based on if it is less than
    or more than the threshold. All fields treated the same. """
    try:
        arcpy.env.overwriteOutput = True
        desc_in_fc = arcpy.Describe(in_fc)
        workspace = desc_in_fc.catalogPath
        fields_list = scoring_fields
        new_score_fields = [
            arcpy.ValidateFieldName("SCORE_{0}".format(str(i).replace("DIST_", "", 1).replace("ANGLE_", "", 1)),
                                    workspace) for i in fields_list]
        arc_print("Adding and Computing Score Fields.", True)
        for new_score_pair in zip(fields_list,new_score_fields):
            field_to_score= new_score_pair[0]
            new_score=new_score_pair[1]
            add_new_field(in_fc, new_score, "DOUBLE", field_alias=new_score)
            arc_print("Computing score for field {0}. Returning {1} if value <= {2} and >= {3}, and {4} otherwise.".format(
                    str(new_score),str(if_less_score),str(threshold_upper),str(threshold_lower),str(if_more_score)),True)
            try:
                with arcpy.da.UpdateCursor(in_fc,[field_to_score,new_score]) as cursor:
                    for row in cursor:
                        row[1]=score_value(row[0],threshold_upper,threshold_lower,if_less_score,if_more_score)
                        cursor.updateRow(row)
            except:
                arc_print("Could not process field {0}".format(new_score))

    except Exception as e:
        arc_print(str(e.args[0]))
        print(e.args[0])


# End do_analysis function

# This test allows the script to be used from the operating
# system command prompt (stand-alone), in a Python IDE,
# as a geoprocessing script tool, or as a module imported in
# another script
if __name__ == '__main__':
    # Define input parameters
    input_features = arcpy.GetParameterAsText(0)
    score_fields = str(arcpy.GetParameterAsText(1)).split(";")
    threshold_upper = arcpy.GetParameter(2)
    threshold_lower = arcpy.GetParameter(3)
    if_within_score = arcpy.GetParameter(4)
    if_outside_score = arcpy.GetParameter(5)
    chained_scoring_func(input_features, score_fields, threshold_upper, threshold_lower, if_within_score, if_outside_score)
