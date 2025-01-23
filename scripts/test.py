import argparse
from ras_docker.arg_parser import get_parser, parse_args
from ras_docker.vcs import test

def test_func(args : argparse.Namespace):
    # docker_check_image_exists(f"ras_{args.app}_app:ras_local")
    # pull_from_docker_repo_if_not_exists(f"ras_{args.app}_app")
    pass


def main():
    test()
    # parser = get_parser(test_func_en=True)
    # parse_args(parser,test_func)
    
if __name__ == "__main__":
    main()
