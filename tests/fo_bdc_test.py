#!/usr/bin/env python

import argparse, time
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

parser.add_argument("-k", "--api_key", 
                    type=str,
                    default=None,
                    help="keep this secret too")

parser.add_argument("-i", "--organization_id", 
                    type=str,
                    default=None,
                    help="if not provided, will get an org list")

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
    
    end = time.time()

    if args.verbosity > 0:
        print "Running time: {:.2f} seconds.".format(end-start)
        
        if args.verbsotiy > 5:
            print "sesh is your fo_bdc.BDCSession object:"
            import ipdb;ipdb.set_trace()
