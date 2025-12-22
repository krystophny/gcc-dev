! Test with only scheduler_header.f90 include
module scheduler_module
  use list_module
  use intlist_module
  use mpiprovider_module
  use matrix_module
  use clientStatus_module
  use workunit_module
  use wuDataRequester_module
  use initWorkunit_module
  use wulist_module

  implicit none

  include "scheduler_header.f90"

contains
  ! Empty contains - no generic or specific includes
  subroutine dummy()
  end subroutine

end module scheduler_module
