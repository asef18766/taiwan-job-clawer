import argparse
from onjobtraining_lib import create_sess, add_course
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("account",  help="user account, usually national identification number")
    parser.add_argument("password", help="user password bj4")
    parser.add_argument("month",    help="the month they had courses", type=int)
    parser.add_argument("days",     help="the days they had courses")
    parser.add_argument("duration", help="the hours in day they had courses")
    args = parser.parse_args()
    
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