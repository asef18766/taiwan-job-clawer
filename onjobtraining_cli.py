import argparse
from onjobtraining_lib import create_sess, add_course
from utils import create_logger_to_file
from os import chdir
from datetime import datetime

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("account",  help="user account, usually national identification number")
    parser.add_argument("password", help="user password bj4")
    parser.add_argument("month",    help="the month they had courses", type=int)
    parser.add_argument("days",     help="the days they had courses")
    parser.add_argument("duration", help="the hours in day they had courses")
    parser.add_argument("work_dir", help="working directory")
    args = parser.parse_args()
    
    chdir(args.work_dir)    
    create_logger_to_file(datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ".log2")
    
    sess = create_sess(
            args.account,
            args.password
        )
    
    usr_c_dates = [(2022, args.month, int(d)) for d in args.days.split(",")]
    usr_c_tp = tuple(tuple(map(int, i.split(":")))
                        for i in args.duration.split("~"))

    add_course(sess, usr_c_dates, usr_c_tp)

if __name__ == "__main__":
    main()