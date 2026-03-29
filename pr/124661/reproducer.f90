module tools
    implicit none
    type point_t
        real :: coords(1:3)
    end type point_t
    type intermediary_t
        type(point_t), allocatable :: ac(:)
    end type intermediary_t
    type point_cloud_t
        type(intermediary_t), allocatable :: points(:)
    contains
        procedure :: init_point_cloud
    end type point_cloud_t
contains
    subroutine init_point_cloud(c)
        class(point_cloud_t) :: c
        allocate (c%points(1))
        allocate (c%points(1)%ac(1))
        print *, c%points(1)%ac(1)%coords(3)
        print *, c%points(1)%ac(1)%coords
   end subroutine init_point_cloud
end module tools
program scatci_integrals
    use tools, only: point_cloud_t
    implicit none
    type(point_cloud_t) :: c
    call c%init_point_cloud
end program scatci_integrals
