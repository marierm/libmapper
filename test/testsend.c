#include "../src/operations.h"
#include "../src/expression.h"
#include "../src/mapper_internal.h"
#include <mapper/mapper.h>
#include <stdio.h>
#include <math.h>

#include <unistd.h>
#include <arpa/inet.h>

int test_controller()
{
    mapper_device md = mdev_new("tester", 9000);
    if (!md) goto error;
    printf("Mapper device created.\n");

    mapper_signal sig =
        msig_float(1, "/testsig", 0, INFINITY, INFINITY, 0, 0, 0);

    mdev_register_output(md, sig);

    printf("Output signal /testsig registered.\n");

    printf("Number of outputs: %d\n", mdev_num_outputs(md));

    const char *host = "localhost";
    int port = 9000;
    mapper_router rt = mapper_router_new(host, port,"TARGET");
    mdev_add_router(md, rt);
    printf("Router to %s:%d added.\n", host, port);

    mapper_router_add_direct_mapping(rt, sig, "/mapped1");
    mapper_router_add_direct_mapping(rt, sig, "/mapped2");

    printf("Polling device..\n");
    int i;
    for (i=0; i<10; i++) {
        mdev_poll(md, 500);
        printf("Updating signal %s to %f\n", sig->name, (i*1.0f));
        msig_update_scalar(sig, (mval)(i*1.0f));
    }

    mdev_remove_router(md, rt);
    printf("Router removed.\n");

    mdev_free(md);
    return 0;

  error:
    if (md) mdev_free(md);
    return 1;
}

int main()
{
    int result = test_controller();
    if (result) {
        printf("Test FAILED.\n");
        return 1;
    }

    printf("Test PASSED.\n");
    return 0;
}
