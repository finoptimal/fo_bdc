#!/usr/bin/env python

import argparse, json, time
import fo_bdc

parser = argparse.ArgumentParser()

parser.add_argument("-u", "--username", 
                    type=str,
                    default=None,
                    help="generally an email address")

parser.add_argument("-p", "--password", 
                    type=str,
                    default=None,
                    help="keep this secret")

parser.add_argument("-i", "--organization_id", 
                    type=str,
                    default=None,
                    help="if not provided, will get an org list")

parser.add_argument("-k", "--api_key", 
                    type=str,
                    default=None,
                    help="keep this secret too")

parser.add_argument("-O", "--logout", 
                    action="store_false",
                    default=True,
                    help="logout when done")

parser.add_argument("-l", "--list",
                    type=str,
                    nargs="*",
                    default=None,
                    help="needs object type at least")

parser.add_argument("-r", "--read", 
                    type=str,
                    nargs=2,
                    default=None,
                    help="needs object_type and object_id")

parser.add_argument("-v", "--verbosity", 
                    type=int,
                    default=1,
                    help="How loud to be")

if __name__=='__main__':
    start = time.time()
    args = parser.parse_args()

    sesh = fo_bdc.BDCSession(args.username, args.password, args.api_key,
                             organization_id=args.organization_id,
                             verbosity=args.verbosity)

    if args.read:
        rd = sesh.read(*args.read)
        print rd

    if args.list:
        rd = sesh.list(*args.list)
        print json.dumps(rd, indent=4)        

    if args.logout:
        sesh.logout()
    
    end = time.time()

    if args.verbosity > 0:
        print "Running time: {:.2f} seconds.".format(end-start)
