#!/bin/bash                                                                     

# $1 is the case path                                                           


# Get times script, gets all of the time directories to be used by mapCase                                               
ls $1 | grep -E '^[0-9]'