Installation
============

1. Navigate to Apps
2. Find with keyword 'to_attendance_device'
3. Install it as usual then you are done

Concepts
========

#. **Machine Position**: is a model to store locations where your attendance machines are installed.
   Each location consists of the following information

   * Name: the name of the location.
   * Time zone: the time zone of the location. This is to support for attendance logs at multiple locations of different time zones

#. **Attendance State**: is a model to store states of attendance activity that can be defined by users.
   States could be Check in, Check out, Overtime Check in, Overtime Start, etc. Please navigate to
   Attendance > Configuration > Attendance Status to see the list of default states that were created
   during installation of this application.
#. **Attendance Activity**: is a model that classifies attendances in activities such as Normal Working, Overtime, etc.
   Navigate to Attendance > Configuration > Attendance Activity to see the list of default activities that were created during installation of this application. Each Attendance Activity is defined with the following

   * Name: the unique name of the activity
   * Attendance Status: List of the attendance states that are applied to this Activity.

#. **Machine User** is a model that stores all the machines' users in your Odoo instance and map such the users with Employees
   in the system. Each Machine User consists of (but not limited to) the following information

   * Name: The name of the user stored in the machine
   * Attendance Machine: The machine to which this user belong
   * UID: The ID (technical field) of the user in the machine storage, which is usually invisible at the machine's inteface/screen
   * ID Number: The ID Number of the user/employee in the machine storage. It is also known as "User ID" in some machines
   * Employee: the employee that is mapped with this user. If you have multiple machines, each employee may map with multiple corresponding machine users

#. **User Attendance**: is a model that stores all the attendance records downloaded from all the machines. In other words,
   it a central database of attendance logs for all your machines. This log will be used as the based to create HR Attendance.
   During that creation, the software will also check for a validity of the attendance to ensure that the HR Attendance data
   is clean and valid.
#. **HR Attendance**: is a model offered by the Odoo's standard module `hr_attendance` and is extended to have the following fields

   * Check In: the time of check in
   * Check Out: the time of check out
   * Employee: the related employee
   * Checkin Machine: the attendance machine that logged the check in
   * Checkout Machine: the attendance machine that logged the check out

   HR Attendance records is created automatically and periodically by the Scheduled Action named "Synchronize attendances scheduler"

#. Employee: is a model in Odoo that is extended for additional following information

   * Unmapped Machines: to show the list of attendance machines that have not get this employee mapped
   * Created from Machine: to indicate if the employee profile was created from machine (i.g. Download users -> auto create employee
     -> au map them). This will helps you filter your employees to see ones that were or were not created from machines

#. **Attendance Machine**: is a model that store all the information of an attendance machine. It also provides a lot of tools such as

   * Upload Users: to upload all your employee to an attendance machine (e.g an new and fresh machine)
   * Download Users: to download all the machine's users data into odoo and map those users with employees (if auto mapping is set)
   * Map Employee: to map machine users with employees in your Odoo instance
   * Check connection: to check if your Odoo instance could connect to the machine
   * Get Machine Info: to get the most important information about the machine (e.g. OEM Vendor, Machine Name, Serial Number, Firmware Version, etc)
   * Download Attendance: to download manually all the attendance data from the machine into your Odoo database, although this could be done automatically be the scheduled action named "Download attendances scheduler"
   * Restart: to restart the machine
   * Clear Data: this is to empty your data. It is very DANGEROUS function and is visible to and accessible by the HR Attendance
     Manager only
   * And many more...

Setup a new attendance machine
==============================
#. Navigate to **Attendances > Attendance Machines > Machines Manager**
#. Click Create button to open machine form view
#. Input the name of the machine (optional)
#. Enter the IP of the machine. It must be accessible from your Odoo server.
   If your Odoo instance is on the Internet while the machine is in your office,
   behind a router, please insure that port forwarding is enabled and the machine's network configuration is
   properly set to allow accessing your machine from outside via Internet. You may need to refer to your router manufacturers for documentation on how to do NAT / port forwarding
#. Port: the port of the machine. It is usually 4370
#. Protocol: which is either UDP or TCP. Most the modern machines nowadays support both. TCP is more reliable but may not be supported by a behind-a-decade machine
#. Location: the location where the machine is physically installed. It is important that the time zone of the location should be correct.
#. You may want to see other options (e.g. Map Employee Before Download, Time zone, Generate Employees During Mapping, etc)
#. Hit Save button to create a new machine in your Odoo.
#. Hit Check Connection to test if the connection works. If it did not work, please troubleshoot for the following cases

   * Check network setting inside the physical machine: IP, Gateway, Port, Net Mask
   * Check your firewall / router to see if it blocks connection from your Odoo instance.
   * Try on switching between UDP and TCP

#. Map Machines Users and Employees

   * If this is a fresh machine without any data stored inside:

     * Hit Upload users

   * If this is not a fresh machine,

     * you may want to Clear Data before doing the step 10.1 mentioned above
     * Or, you may want to Download Users and map them to existing employee or create a new employee accordingly

   * Validate the result:

     * All Machine Users should link to a corresponding employee
     * No unmapped employees shown on the machine form view

#. Test Attendance Data download and synchronization

   * Do some check-in and check out at the physical machine

     * Wait for seconds between check in and check out
     * Try some wrong actions: check in a few times before check out

   * Come back to the machine form view in Odoo

     * Hit Download Attendance Data and wait for its completion. For just a few attendance records, it may take only a couple
       of seconds even your device is located in a country other than the Odoo instance's

   * Validate the result

     * Navigating to **Attendances > Attendance Machines > Attendance Data** to validate if the attendance log is recorded there.
     * If found, you are done now. You can continue with the following steps to bring the new machine into production

       * Clear the sample attendance data you have created:

         * Navigate to Attendances > Attendance Machines > Attendance Data, find and delete those sample records
         * Navigate to Attendances > Attendance Machines > Synchronize and hit Clear Attendance Data button

       * Hit the Confirmed state in the header of the machine form view. If you don't do it, the schedulers will ignore the machine during their runs

     * If not found, there should be some trouble that need further investigation

       * Check the connection
       * Try to get the machine information
       * Check the work codes of the machine if they are match with the ones specified in the "Attendance Status Codes" table
         in the machine form view
       * Contact the author of the "Attendance Machine" application if you could not solve the problem your self.

Set up for a new Employee
=========================
#. Create an employee as usual
#. Hit the Action button in the header area of the employee form view to find the menu item "Upload to Attendance Machine"
   in the dropped down list
#. Select the machine(s) that will be used for this employee then hit Upload Employees button
#. You can also do mass upload by selecting employees from the employee list view. Or go to the machines

How the automation works
========================

There are two schedule actions:

#. **Download attendances scheduler**: By default, it runs every 30 minutes to

   * Download the attendance log/data from all your machines that are set in Confirmed status. Machines that are not in this status will be ignored
   * Create User Attendance records in your Odoo database
   * Depending on the configuration you made on the machines, it may also do the following automatically

     * Create new employees and map with the corresponding machine users if new users are found in the machines
     * Clear the attendance data from the machine if it's time to do it.

#. **Synchronize attendances scheduler**: By default, it runs every 30 minutes to

   * find the valid attendance in the user attendance log
   * create HR Attendance records from such the log
